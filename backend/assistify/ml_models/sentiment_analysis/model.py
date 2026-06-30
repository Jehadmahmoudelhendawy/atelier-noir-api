import logging
import torch
import gc
from typing import Dict, Any
from transformers import AutoTokenizer, AutoModelForSequenceClassification
logger = logging.getLogger(__name__)
class SentimentAnalysisModel:
    SENTIMENT_MAP = {
        0: 'negative',
        1: 'neutral',
        2: 'positive'
    }
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cpu") 
        self._load_model()
    def _load_model(self):
        try:
            logger.info(f"Loading Sentiment Analysis model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                low_cpu_mem_usage=True,
                device_map=None,
                torch_dtype=torch.float32 
            )
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            logger.error(f"Error loading Sentiment model: {e}")
            self.model = None
    def predict(self, text: str) -> Dict[str, Any]:
        if not self.model or not self.tokenizer:
            return self._keyword_only_predict(text)
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits.detach().cpu()
                probs = torch.nn.functional.softmax(logits, dim=-1)
                confidence, label_idx = torch.max(probs, dim=-1)
            sentiment = self.SENTIMENT_MAP.get(label_idx.item(), 'neutral')
            return {
                'sentiment': sentiment,
                'confidence': float(confidence.item()),
                'label_idx': int(label_idx.item())
            }
        except Exception as e:
            logger.error(f"Error in Sentiment prediction: {e}")
            return self._keyword_only_predict(text)
    def _keyword_only_predict(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        positive_words = ['good', 'great', 'happy', 'excellent', 'thanks', 'thank', 'جيد', 'ممتاز', 'شكرا']
        negative_words = ['bad', 'poor', 'unhappy', 'broken', 'wrong', 'issue', 'سيء', 'مشكلة', 'خطأ']
        if any(w in text_lower for w in positive_words):
            return {'sentiment': 'positive', 'confidence': 0.5, 'label_idx': 2}
        if any(w in text_lower for w in negative_words):
            return {'sentiment': 'negative', 'confidence': 0.5, 'label_idx': 0}
        return {'sentiment': 'neutral', 'confidence': 0.1, 'label_idx': 1}
    def __del__(self):
        if hasattr(self, 'model'): del self.model
        if hasattr(self, 'tokenizer'): del self.tokenizer
        gc.collect()