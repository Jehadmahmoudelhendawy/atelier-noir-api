import unittest
from unittest.mock import Mock, patch
from .intent_classification.model import IntentClassificationModel
from .sentiment_analysis.model import SentimentAnalysisModel
from .response_generation.model import ResponseGenerationModel
from .product_recommendation.model import ProductRecommendationModel
from .orchestrator import ModelOrchestrator, ModelContext
class TestIntentClassification(unittest.TestCase):
    def setUp(self):
        self.model = IntentClassificationModel()
    def test_greeting_intent(self):
        result = self.model.predict("hello")
        self.assertEqual(result['intent'], 'greeting')
        self.assertGreater(result['confidence'], 0.5)
    def test_purchase_intent(self):
        result = self.model.predict("I want to buy a device")
        self.assertEqual(result['intent'], 'purchase')
        self.assertGreater(result['confidence'], 0.5)
    def test_offer_intent(self):
        result = self.model.predict("What are your discounts?")
        self.assertEqual(result['intent'], 'offer')
        self.assertGreater(result['confidence'], 0.5)
    def test_order_tracking_intent(self):
        result = self.model.predict("Track my order")
        self.assertEqual(result['intent'], 'order_tracking')
        self.assertGreater(result['confidence'], 0.5)
    def test_arabic_greeting(self):
        result = self.model.predict("مرحبا")
        self.assertEqual(result['intent'], 'greeting')
        self.assertGreater(result['confidence'], 0.5)
    def test_unknown_intent_defaults_to_inquiry(self):
        result = self.model.predict("xyz123abc")
        self.assertEqual(result['intent'], 'inquiry')
class TestSentimentAnalysis(unittest.TestCase):
    def setUp(self):
        self.model = SentimentAnalysisModel()
    def test_positive_sentiment(self):
        result = self.model.predict("This product is amazing!")
        self.assertEqual(result['sentiment'], 'positive')
        self.assertGreater(result['confidence'], 0.5)
    def test_negative_sentiment(self):
        result = self.model.predict("This product is terrible")
        self.assertEqual(result['sentiment'], 'negative')
        self.assertGreater(result['confidence'], 0.5)
    def test_neutral_sentiment(self):
        result = self.model.predict("What is the price?")
        self.assertEqual(result['sentiment'], 'neutral')
        self.assertGreater(result['confidence'], 0.5)
    def test_arabic_positive(self):
        result = self.model.predict("رائع جداً")
        self.assertEqual(result['sentiment'], 'positive')
    def test_arabic_negative(self):
        result = self.model.predict("سيء جداً")
        self.assertEqual(result['sentiment'], 'negative')
class TestResponseGeneration(unittest.TestCase):
    def setUp(self):
        self.model = ResponseGenerationModel()
    def test_greeting_response(self):
        result = self.model.generate("hello", context={'intent': 'greeting'})
        self.assertIn('Welcome', result['response'])
        self.assertGreater(result['confidence'], 0.5)
    def test_purchase_response(self):
        result = self.model.generate("buy device", context={'intent': 'purchase'})
        self.assertIn('find', result['response'].lower())
    def test_response_with_recommendations(self):
        recommendations = [
            {'name': 'Product 1', 'price': 100},
            {'name': 'Product 2', 'price': 200}
        ]
        result = self.model.generate(
            "buy",
            context={
                'intent': 'purchase',
                'recommendations': recommendations
            }
        )
        self.assertIn('Product 1', result['response'])
    def test_response_with_negative_sentiment(self):
        result = self.model.generate(
            "bad product",
            context={'sentiment': 'negative'}
        )
        self.assertIn('concern', result['response'].lower())
class TestProductRecommendation(unittest.TestCase):
    def setUp(self):
        self.model = ProductRecommendationModel()
    @patch('assistify.ml_models.product_recommendation.model.Product')
    def test_purchase_recommendations(self, mock_product):
        mock_product.objects.filter.return_value = []
        result = self.model.predict(intent='purchase')
        self.assertIsInstance(result['recommendations'], list)
        self.assertIn('count', result)
    def test_recommendation_structure(self):
        result = self.model.predict(intent='purchase')
        if result['recommendations']:
            rec = result['recommendations'][0]
            self.assertIn('product_id', rec)
            self.assertIn('name', rec)
            self.assertIn('price', rec)
            self.assertIn('score', rec)
class TestModelContext(unittest.TestCase):
    def test_context_creation(self):
        context = ModelContext(user_id=1, message="test")
        self.assertEqual(context.user_id, 1)
        self.assertEqual(context.message, "test")
        self.assertIsNone(context.intent)
    def test_context_to_dict(self):
        context = ModelContext(user_id=1, message="test")
        context.intent = {'intent': 'purchase'}
        context_dict = context.to_dict()
        self.assertIn('user_id', context_dict)
        self.assertIn('intent', context_dict)
class TestModelOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = ModelOrchestrator()
    def test_orchestrator_singleton(self):
        orch1 = ModelOrchestrator()
        orch2 = ModelOrchestrator()
        self.assertIs(orch1, orch2)
    def test_process_message_success(self):
        result = self.orchestrator.process_message(
            user_id=1,
            message="hello"
        )
        self.assertTrue(result['success'])
        self.assertIn('response', result)
        self.assertIn('intent', result)
        self.assertIn('sentiment', result)
    def test_process_message_with_purchase_intent(self):
        result = self.orchestrator.process_message(
            user_id=1,
            message="I want to buy a device"
        )
        self.assertEqual(result['intent'], 'purchase')
    def test_process_message_with_positive_sentiment(self):
        result = self.orchestrator.process_message(
            user_id=1,
            message="I love this product"
        )
        self.assertEqual(result['sentiment'], 'positive')
    def test_get_model_status(self):
        status = self.orchestrator.get_model_status()
        self.assertEqual(status['status'], 'operational')
        self.assertIn('intent_model', status)
        self.assertIn('sentiment_model', status)
    def test_classify_intent(self):
        result = self.orchestrator._classify_intent("hello")
        self.assertIn('intent', result)
        self.assertIn('confidence', result)
    def test_analyze_sentiment(self):
        result = self.orchestrator._analyze_sentiment("great!")
        self.assertIn('sentiment', result)
        self.assertIn('confidence', result)
    def test_get_recommendations(self):
        recommendations = self.orchestrator._get_recommendations(
            user_id=1,
            intent='purchase'
        )
        self.assertIsInstance(recommendations, list)
    def test_generate_response(self):
        response = self.orchestrator._generate_response(
            message="hello",
            intent="greeting",
            sentiment="neutral",
            recommendations=[]
        )
        self.assertIn('response', response)
        self.assertIn('confidence', response)
class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.orchestrator = ModelOrchestrator()
    def test_full_pipeline_greeting(self):
        result = self.orchestrator.process_message(
            user_id=1,
            message="Hello, how are you?"
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['intent'], 'greeting')
        self.assertIsNotNone(result['response'])
    def test_full_pipeline_purchase(self):
        result = self.orchestrator.process_message(
            user_id=1,
            message="I want to buy a blood pressure monitor"
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['intent'], 'purchase')
        self.assertIsNotNone(result['response'])
    def test_full_pipeline_complaint(self):
        result = self.orchestrator.process_message(
            user_id=1,
            message="This product is broken!"
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['sentiment'], 'negative')
    def test_full_pipeline_arabic(self):
        result = self.orchestrator.process_message(
            user_id=1,
            message="أريد شراء جهاز قياس ضغط الدم"
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['response'])
if __name__ == '__main__':
    unittest.main()