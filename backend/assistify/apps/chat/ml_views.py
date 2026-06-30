from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from assistify.ml_models.orchestrator import ModelOrchestrator
import logging
logger = logging.getLogger(__name__)
class MLPipelineView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            orchestrator = ModelOrchestrator()
            user_id = request.user.id if request.user.is_authenticated else None
            result = orchestrator.process_message(user_id=user_id, message=message)
            return Response({
                'success': result.get('success'),
                'response': result.get('response'),
                'reply': result.get('response'),
                'message': result.get('response'),
                'intent': result.get('intent'),
                'sentiment': result.get('sentiment'),
                'recommendations': result.get('recommendations', []),
                'confidence': {
                    'intent': result.get('intent_confidence'),
                    'sentiment': result.get('sentiment_confidence')
                },
                'metadata': result.get('metadata', {})
            })
        except Exception as e:
            logger.error(f"Error in ML pipeline: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class IntentClassificationView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            orchestrator = ModelOrchestrator()
            result = orchestrator._classify_intent_safe(message)
            return Response({
                'intent': result.get('intent'),
                'confidence': result.get('confidence'),
                'label_idx': result.get('label_idx')
            })
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class SentimentAnalysisView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            orchestrator = ModelOrchestrator()
            result = orchestrator._analyze_sentiment_safe(message)
            return Response({
                'sentiment': result.get('sentiment'),
                'confidence': result.get('confidence'),
                'label_idx': result.get('label_idx')
            })
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class RecommendationView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        query = request.data.get('query', '')
        intent = request.data.get('intent', 'inquiry')
        try:
            orchestrator = ModelOrchestrator()
            user_id = request.user.id if request.user.is_authenticated else None
            recommendations, method = orchestrator._get_recommendations_stable(
                user_id=user_id,
                intent=intent,
                query=query
            )
            return Response({
                'recommendations': recommendations,
                'count': len(recommendations),
                'method': method
            })
        except Exception as e:
            logger.error(f"Error in recommendations: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ModelStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        try:
            orchestrator = ModelOrchestrator()
            status_info = orchestrator.get_model_status()
            return Response({
                'status': 'operational',
                'info': status_info
            })
        except Exception as e:
            logger.error(f"Error getting model status: {e}")
            return Response(
                {'status': 'error', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )