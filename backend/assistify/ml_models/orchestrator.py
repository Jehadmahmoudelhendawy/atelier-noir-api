import requests
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

class SignalBundle:
    pass

class PurchaseState:
    IDLE = "idle"

class ModelOrchestrator:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
        import os
        # The chatbot microservice URL. Override with MICROSERVICE_URL on the
        # demo's separate backend so it talks to its own chatbot instance.
        self.microservice_url = os.getenv("MICROSERVICE_URL", "https://assistify-system.vercel.app/chat")
        self._initialized = True

    def process_message(
        self,
        message: str,
        conversation_id: Optional[int] = None,
        user_id: Optional[int] = None,
        source: str = "web",
        **kwargs,
    ) -> Dict[str, Any]:
        text = message or kwargs.get("text", "")
        if not text.strip():
            return {"success": False, "error": "Empty message"}
            
        try:
            payload = {
                "message": text,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "source": source
            }
            response = requests.post(self.microservice_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", ""),
                "intent": data.get("intent", "inquiry"),
                "sentiment": data.get("sentiment", "neutral"),
                "recommendations": data.get("recommendations", []),
                "confidence": data.get("confidence", {"intent": 0.99, "sentiment": 0.99}),
                "metadata": data.get("metadata", {})
            }
        except Exception as e:
            logger.error(f"Error communicating with Chatbot Microservice: {e}", exc_info=True)
            return {
                "success": False,
                "response": "عذراً، خدمة المحادثة غير متاحة حالياً. الرجاء المحاولة لاحقاً.",
                "error": str(e)
            }

    def _classify_intent_safe(self, message: str) -> Dict[str, Any]:
        return {"intent": "inquiry", "confidence": 0.99, "label_idx": 0}

    def _analyze_sentiment_safe(self, message: str) -> Dict[str, Any]:
        return {"sentiment": "neutral", "confidence": 0.99, "label_idx": 1}

    def _get_recommendations_stable(self, user_id: Optional[int], intent: str, query: str) -> Tuple[List[Dict], str]:
        return [], "microservice_proxy"

    def get_model_status(self) -> Dict[str, Any]:
        return {
            "status": "operational",
            "intent_model": True,
            "sentiment_model": True,
            "recommendation_model": True,
            "generation_model": True,
            "backend": "microservice_proxy"
        }