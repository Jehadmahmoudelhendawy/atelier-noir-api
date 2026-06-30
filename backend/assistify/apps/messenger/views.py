import json
import logging
import requests
import threading
from django.conf import settings
from decouple import config
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from assistify.apps.chat.models import Conversation, Message
from assistify.apps.chat.service import get_chat_response

logger = logging.getLogger(__name__)

class MessengerWebhookView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        verify_token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        mode = request.query_params.get("hub.mode")
        
        MESSENGER_VERIFY_TOKEN = config("MESSENGER_VERIFY_TOKEN", default="")

        if mode and verify_token:
            if mode == "subscribe" and verify_token == MESSENGER_VERIFY_TOKEN:
                logger.info("WEBHOOK_VERIFIED")
                return Response(int(challenge), status=status.HTTP_200_OK)
            else:
                return Response("Verification failed", status=status.HTTP_403_FORBIDDEN)
        return Response("Hello from Messenger Webhook", status=status.HTTP_200_OK)

    def post(self, request):
        try:
            data = request.data
            if data.get("object") == "page":
                for entry in data.get("entry", []):
                    for messaging_event in entry.get("messaging", []):
                        if "message" in messaging_event and "text" in messaging_event["message"]:
                            sender_id = messaging_event["sender"]["id"]
                            message_text = messaging_event["message"]["text"]
                            
                            self.process_message(sender_id, message_text)
                return Response("EVENT_RECEIVED", status=status.HTTP_200_OK)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error handling messenger webhook: {e}", exc_info=True)
            return Response("Internal Error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_message(self, sender_id, message_text):
        try:
            logger.info(f"Processing message for {sender_id}: {message_text}")
            session_key = f"messenger_{sender_id}"
            conversation, _ = Conversation.objects.get_or_create(session_key=session_key)

            Message.objects.create(
                conversation=conversation, 
                role=Message.Role.USER, 
                content=message_text
            )

            result = get_chat_response(message_text, conversation_id=conversation.id, source="messenger")
            bot_reply = result.get('response', '')
            
            logger.info(f"Got AI reply for {sender_id}")

            Message.objects.create(
                conversation=conversation, 
                role=Message.Role.ASSISTANT, 
                content=bot_reply
            )

            self.send_messenger_reply(sender_id, bot_reply)
        except Exception as e:
            logger.error(f"Error processing messenger message: {e}", exc_info=True)

    def send_messenger_reply(self, recipient_id, message_text):
        MESSENGER_PAGE_ACCESS_TOKEN = config("MESSENGER_PAGE_ACCESS_TOKEN", default="")
        if not MESSENGER_PAGE_ACCESS_TOKEN:
            logger.error("MESSENGER_PAGE_ACCESS_TOKEN is not configured in .env")
            return

        url = f"https://graph.facebook.com/v19.0/me/messages?access_token={MESSENGER_PAGE_ACCESS_TOKEN}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "recipient": {"id": recipient_id},
            "messaging_type": "RESPONSE",
            "message": {"text": message_text}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to send message via Messenger API. Status: {response.status_code}, Error: {response.text}")
            else:
                logger.info(f"Successfully sent reply to Messenger sender {recipient_id}")
        except Exception as e:
            logger.error(f"Error sending message to Facebook: {e}", exc_info=True)

