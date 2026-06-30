import re
import json
import threading
import logging
from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from decouple import config
from .models import Conversation, Message
from .service import get_chat_response, get_model_insights
from assistify.apps.products.models import Product
logger = logging.getLogger(__name__)


# Color synonyms (Arabic + English) -> the Product.color value they refer to.
COLOR_SYNONYMS = {
    "Navy Blue": ["كحلي", "كحلية", "navy"],
    "Midnight Blue": ["ليلي", "midnight"],
    "Royal Blue": ["ملكي", "royal"],
    "Sky Blue": ["سماوي", "sky blue"],
    "Light Blue": ["أزرق فاتح", "ازرق فاتح", "light blue"],
    "Onyx Black": ["أونيكس", "اونيكس", "onyx"],
    "Black": ["أسود", "اسود", "سودا", "سوده", "سودة", "black"],
    "Charcoal": ["رمادي غامق", "charcoal"],
    "Light Grey": ["رمادي فاتح", "light grey", "light gray"],
    "Grey": ["رمادي", "رصاصي", "grey", "gray"],
    "White": ["أبيض", "ابيض", "بيضا", "بيضاء", "white"],
    "Beige": ["بيج", "beige"],
    "Camel": ["جملي", "camel"],
    "Brown": ["بني", "brown"],
    "Oxblood": ["أوكسبلود", "اوكسبلود", "أحمر داكن", "oxblood"],
    "Burgundy": ["نبيتي", "خمري", "برجاندي", "برغندي", "burgundy"],
    "Red": ["أحمر", "احمر", "حمرا", "حمراء", "حمرة", "red"],
    "Emerald": ["زمردي", "أخضر", "اخضر", "خضرا", "خضراء", "emerald"],
    "Pink": ["وردي", "بمبي", "زهري", "pink"],
    "Lavender": ["لافندر", "lavender"],
    "Champagne": ["شامبني", "champagne"],
    "Gold": ["ذهبي", "دهبي", "gold"],
    "Silver": ["فضي", "فضى", "silver"],
    "Nude": ["نود", "بيج فاتح", "nude"],
}

# Item-type synonyms -> how to identify that product type.
# Order matters: more specific types come before generic ones.
TYPE_SYNONYMS = [
    (["توكسيدو", "tuxedo"], {"name": "Tuxedo"}),
    (["بدلة", "بدله", "suit"], {"cat": "suits"}),
    (["بليزر", "blazer"], {"name": "Blazer"}),
    (["بالطو", "معطف", "overcoat", "coat"], {"name": "Overcoat"}),
    (["قميص", "shirt"], {"name": "Dress Shirt"}),
    (["بلوزة", "blouse"], {"name": "Blouse"}),
    (["كوكتيل", "cocktail"], {"name": "Cocktail Dress"}),
    (["فستان سهرة", "gown", "evening dress"], {"name": "Evening Gown"}),
    (["فستان", "dress"], {"cat": "dresses"}),
    (["صندل", "كعب", "هيل", "heel", "sandal"], {"name": "Heeled"}),
    (["أوكسفورد", "اوكسفورد", "حذاء", "جزمة", "جزم", "shoe", "oxford"], {"name": "Oxford"}),
    (["بابيون", "bow tie", "bowtie"], {"name": "Bow Tie"}),
    (["كرافتة", "كرافت", "كرفته", "جرافتة", "جرافته", "جرافت", "قرافتة", "necktie", "tie"], {"name": "Silk Tie"}),
    (["حزام", "belt"], {"name": "Belt"}),
    (["أزرار", "زراير", "cufflink"], {"name": "Cufflinks"}),
    (["منديل", "pocket square", "pocket"], {"name": "Pocket Square"}),
    (["إيشارب", "ايشارب", "وشاح", "scarf"], {"name": "Scarf"}),
]


# Words that introduce a *reference* item ("a tie that goes WITH the suit").
COORDINATION_WORDS = ["تليق", "يليق", "تناسب", "يناسب", "مع ", "على ", "معاها", "معاه", " with ", " for ", "match", "goes with"]
# Words that say an item is already chosen/owned — what follows is context...
SELECTION_WORDS = ["اخترت", "اخترتي", "اختارت", "عندي", "معايا", "معاي", "لابس", "لابسة", "لبست", "هلبس على", "واخد", "واخده", "شريت", "اشتريت", "اشتريتي"]
# ...until a request/question word marks what is actually being asked for.
REQUEST_WORDS = ["البس", "هلبس", "حلبس", "انسب", "أنسب", "اقترح", "اقترحلي", "رشح", "رشحلي", "عايز", "عاوز", "محتاج", "محتاجة", "ايه", "إيه", "انهي", "أنهي", "تنصح", "ينفع"]

MEN_WORDS = ["رجالي", "رجالى", "رجال", "راجل", "رجل", "ولد", "شاب", "عريس", "men ", "men's", "male", "groom", "gentleman", "him", "his"]
WOMEN_WORDS = ["نسائي", "حريمي", "حريمى", "نساء", "امرأة", "امرأه", "سيدة", "سيده", "مدام", "بنت", "بنوتة", "بنوته", "بنوتي", "انسة", "آنسة", "ست ", "عروسة", "عروسه", "عروس", "women", "woman", "female", "girl", "lady", "bride", "her ", "she "]
MEN_TYPE_NAMES = {"Tuxedo", "Blazer", "Overcoat", "Dress Shirt", "Oxford", "Bow Tie", "Silk Tie", "Belt", "Cufflinks", "Pocket Square"}
WOMEN_TYPE_NAMES = {"Blouse", "Cocktail Dress", "Evening Gown", "Heeled"}


def _spec_gender(spec):
    if spec.get("cat") == "suits":
        return "men"
    if spec.get("cat") == "dresses":
        return "women"
    name = spec.get("name", "")
    if name in MEN_TYPE_NAMES:
        return "men"
    if name in WOMEN_TYPE_NAMES:
        return "women"
    return None


def _detect_gender(text, type_specs):
    """Decide whether the shopper means men's or women's items, from explicit
    words first, otherwise from the item types in play. Returns None if unclear."""
    if any(w in text for w in MEN_WORDS):
        return "men"
    if any(w in text for w in WOMEN_WORDS):
        return "women"
    genders = {g for g in (_spec_gender(s) for s in type_specs) if g}
    if len(genders) == 1:
        return next(iter(genders))
    return None


def _product_card(p):
    return {
        "id": p.id,
        "name": p.name,
        "price": float(p.price),
        "currency": p.currency,
        "color": p.color,
        "gender": getattr(p, "gender", "unisex"),
        "image_url": p.image_url,
        "category_display": p.get_category_display(),
    }


def match_products_for_message(message, reply="", limit=5):
    """Pick catalog products to show as cards in the chat.

    Uses BOTH the user's message and the assistant's reply (the reply names the
    specific item types and colors the assistant actually recommended). It
    detects the requested item type(s) and color(s) and returns exactly those —
    e.g. a reply suggesting navy + burgundy + silver ties shows those three
    ties, not every tie. Falls back to keyword overlap if nothing is detected.
    """
    msg = (message or "").lower()
    reply_l = (reply or "").lower()
    text = f"{message or ''} {reply or ''}".lower()
    if not text.strip():
        return []

    # Work out which parts of the QUESTION describe a *reference* item (already
    # chosen / what the new item should match) versus the item being asked for.
    context_spans = []
    # "...that goes WITH the suit": everything after the coordination word.
    coord = [msg.find(w) for w in COORDINATION_WORDS if w in msg]
    if coord:
        context_spans.append((min(coord), len(msg)))
    # "I chose the tie and the suit, which shoes...": from the selection word
    # up to the request word is context; the asked item comes after.
    sel = [msg.find(w) for w in SELECTION_WORDS if w in msg]
    if sel:
        sel_pos = min(sel)
        reqs = [msg.find(w) for w in REQUEST_WORDS if w in msg and msg.find(w) > sel_pos]
        context_spans.append((sel_pos, min(reqs) if reqs else len(msg)))

    def is_context(pos):
        return any(a <= pos < b for a, b in context_spans)

    # Item type: from the asked part of the question first; else from the reply.
    msg_typed = [
        (min(msg.find(s) for s in syns if s in msg), spec)
        for syns, spec in TYPE_SYNONYMS if any(s in msg for s in syns)
    ]
    asked = [spec for pos, spec in msg_typed if not is_context(pos)] or [spec for _p, spec in msg_typed]
    reply_types = [spec for syns, spec in TYPE_SYNONYMS if any(s in text for s in syns)]
    type_specs = asked or reply_types

    # Colors: recommended colors from the reply, plus colors in the asked part
    # of the question (context colors — the suit you already have — are ignored).
    reply_colors = {c for c, syns in COLOR_SYNONYMS.items() if any(s in reply_l for s in syns)}
    msg_colored = [
        (min(msg.find(s) for s in syns if s in msg), c)
        for c, syns in COLOR_SYNONYMS.items() if any(s in msg for s in syns)
    ]
    msg_colors = {c for pos, c in msg_colored if not is_context(pos)}
    colors = reply_colors | msg_colors

    gender = _detect_gender(text, type_specs)

    def is_type(p):
        for spec in type_specs:
            if "cat" in spec and p.category == spec["cat"]:
                return True
            if "name" in spec and spec["name"] in p.name:
                return True
        return False

    if type_specs or colors:
        products = list(Product.objects.filter(is_active=True))

        def gender_ok(p):
            return not gender or getattr(p, "gender", "unisex") in (gender, "unisex")

        def ranked(items):
            items.sort(key=lambda p: float(p.price))
            return [_product_card(p) for p in items[:limit]]

        typed = [p for p in products if (not type_specs or is_type(p)) and gender_ok(p)]
        # 1) Best: the asked type in a recommended color.
        if colors:
            colored = [p for p in typed if p.color in colors]
            if colored:
                return ranked(colored)
        # 2) We know the asked type but none in that exact color — show the
        #    type (any colour) rather than falling back to unrelated items.
        if type_specs and typed:
            return ranked(typed)
        # 3) Only a color was asked (no specific type).
        if colors and not type_specs:
            colored = [p for p in products if p.color in colors and gender_ok(p)]
            if colored:
                return ranked(colored)

    # Fallback: keyword-overlap scoring across name/description/color/category.
    tokens = {t for t in re.split(r"[^\w؀-ۿ]+", text) if len(t) >= 3}
    if not tokens:
        return []
    scored = []
    for p in Product.objects.filter(is_active=True):
        haystack = f"{p.name} {p.description} {p.color} {p.get_category_display()}".lower()
        score = sum(1 for t in tokens if t in haystack)
        if score:
            scored.append((score, float(p.price), p))
    if not scored:
        return []
    best = max(s for s, _p, _o in scored)
    floor = best if best <= 1 else max(2, best - 1)
    top = sorted((x for x in scored if x[0] >= floor), key=lambda x: (-x[0], x[1]))
    return [_product_card(p) for _s, _pr, p in top[:limit]]
class ChatView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        message_text = request.data.get("message", "").strip()
        conversation_id = request.data.get("conversation_id")
        if not message_text:
            return Response({"error": "message is required."}, status=status.HTTP_400_BAD_REQUEST)
        conversation = self._get_or_create_conversation(request, conversation_id)
        Message.objects.create(conversation=conversation, role=Message.Role.USER, content=message_text)
        user_id = request.user.id if request.user.is_authenticated else None
        result = get_chat_response(message_text, user_id=user_id, conversation_id=conversation.id, source="web")
        Message.objects.create(
            conversation=conversation, 
            role=Message.Role.ASSISTANT, 
            content=result.get('response', '')
        )
        response_data = {
            "success": result.get("success", True),
            "response": result.get("response"),
            "reply": result.get("response"),
            "message": result.get("response"),
            "intent": result.get("intent"),
            "sentiment": result.get("sentiment"),
            "recommendations": result.get("recommendations", []),
            "confidence": result.get("confidence", {"intent": 0.0, "sentiment": 0.0}),
            "metadata": result.get("metadata", {"recommendation_method": "none", "user_name": None}),
            "products": match_products_for_message(message_text, result.get("response", "")),
            "conversation_id": conversation.id
        }
        return Response(response_data)
    def _get_or_create_conversation(self, request, conversation_id):
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key or ""
        return Conversation.objects.create(user=user, session_key=session_key)
class ConversationHistoryView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.prefetch_related("messages").get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        messages = [
            {"role": m.role, "content": m.content, "created_at": m.created_at}
            for m in conversation.messages.all()
        ]
        return Response({"conversation_id": conversation.id, "messages": messages})
class WhatsAppWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        message_text = request.data.get("Body", "").strip()
        sender = request.data.get("From", "")
        if not message_text or not sender:
            return HttpResponse("Missing Body or From", status=400)
        phone_number = sender.replace("whatsapp:", "").strip()
        conversation, created = Conversation.objects.get_or_create(session_key=phone_number)
        if not conversation.phone:
            conversation.phone = phone_number
            conversation.save(update_fields=["phone"])
        Message.objects.create(conversation=conversation, role=Message.Role.USER, content=message_text)
        self.process_and_reply(message_text, sender, conversation.id)
        response = MessagingResponse()
        return HttpResponse(str(response), content_type='text/xml')
    def process_and_reply(self, message_text, sender, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            result = get_chat_response(message_text, user_id=None, conversation_id=conversation.id, source="whatsapp")
            reply_text = result.get('response', 'عذراً، أواجه مشكلة في معالجة طلبك الآن.')
            Message.objects.create(
                conversation=conversation, 
                role=Message.Role.ASSISTANT, 
                content=reply_text
            )
            account_sid = config("TWILIO_ACCOUNT_SID", default="")
            auth_token = config("TWILIO_AUTH_TOKEN", default="")
            twilio_number = config("TWILIO_WHATSAPP_NUMBER", default="+14155238886")
            if not twilio_number.startswith("whatsapp:"):
                twilio_number = f"whatsapp:{twilio_number}"
            if account_sid and auth_token:
                client = Client(account_sid, auth_token)
                try:
                    client.messages.create(
                        body=reply_text,
                        from_=twilio_number,
                        to=sender
                    )
                except Exception as twilio_err:
                    logger.error(f"Twilio error (possibly limits reached): {twilio_err}")
                    print("\n" + "="*50)
                    print(f"🤖 [WHATSAPP SIMULATION FALLBACK] Reply to {sender}:")
                    print(reply_text)
                    print("="*50 + "\n")
            else:
                logger.error("Twilio credentials missing from .env. Could not send async reply.")
        except Exception as e:
            logger.error(f"WhatsApp Background Pipeline Error: {e}", exc_info=True)