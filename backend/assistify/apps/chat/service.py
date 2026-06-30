from assistify.apps.products.models import Product, Offer
from assistify.ml_models.orchestrator import ModelOrchestrator
import logging
logger = logging.getLogger(__name__)
def get_orchestrator():
    return ModelOrchestrator()
def get_chat_response(message: str, user_id=None, conversation_id=None, source="web") -> dict:
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.process_message(
            message=message, 
            user_id=user_id, 
            conversation_id=conversation_id,
            source=source
        )
        if result.get('success'):
            return result
        else:
            logger.error(f"Orchestrator error: {result.get('error')}")
            return _get_fallback_result(message)
    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}", exc_info=True)
        return _get_fallback_result(message)
def _get_fallback_result(message: str) -> dict:
    return {
        "success": True,
        "response": "أنا مساعد الأناقة في Atelier Noir 😊 أقدر أساعدك في المنتجات، الطلبات، التتبع، أو الشكاوى. تحبي أساعدك في إيه؟",
        "intent": "inquiry",
        "sentiment": "neutral",
        "recommendations": [],
        "confidence": {"intent": 0.1, "sentiment": 0.1},
        "metadata": {"recommendation_method": "none", "user_name": None}
    }
def get_model_insights(message: str, user_id=None, source="web") -> dict:
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.process_message(user_id=user_id, message=message, source=source)
        return {
            'intent': result.get('intent'),
            'sentiment': result.get('sentiment'),
            'recommendations': result.get('recommendations', []),
            'confidence': result.get('confidence', {})
        }
    except Exception as e:
        logger.error(f"Error getting model insights: {e}")
        return {}