from __future__ import annotations
import gc
import json
import logging
import os
import re
from typing import Any, Dict, Optional
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
logger = logging.getLogger(__name__)
_DEFAULT_INTENT_MAP: Dict[str, int] = {
    'inquiry': 0, 'greeting': 1, 'offer': 2, 'order_tracking': 3, 'payment': 4,
    'return': 5, 'product_search': 6, 'purchase': 7, 'complaint': 8, 'support': 9,
    'feedback': 10, 'goodbye': 11, 'recommendation_request': 12, 'introduce_name': 13,
    'memory_check': 14, 'product_details': 15, 'recommendation_reasoning': 16, 'confirmation': 17,
}
_KEYWORD_BOOSTS: Dict[str, list] = {
    'order_tracking': ['تتبع', 'فين طلبي', 'حالة الطلب', 'track', 'order status', 'where is my order', 'ord-'],
    'recommendation_reasoning': ['ليه', 'اشمعنى', 'بناء على ايه', 'سبب', 'why', 'reason', 'why this', 'why recommended'],
    'memory_check': ['اسمي إيه', 'اسمي ايه', 'مين أنا', 'انا مين', 'who am i', "what's my name", 'what is my name'],
    'introduce_name': ['اسمي', 'معاك', 'أنا اسمي', 'my name is', "i'm", 'i am', 'this is', 'call me'],
    'purchase': ['هشتري', 'هطلبه', 'اشتري', 'اطلبه', 'عايز اشتري', 'buy', 'order this', 'purchase', "i'll take it"],
    'product_details': ['تفاصيل', 'معلومات', 'سعره', 'بكام', 'مواصفات', 'مميزاته', 'details', 'how much', 'specs', 'tell me more'],
    'greeting': ['أهلاً', 'مرحبا', 'هاي', 'صباح الخير', 'مساء الخير', 'hello', 'hi', 'hey', 'good morning'],
    'goodbye': ['شكراً', 'مع السلامة', 'سلام', 'تسلم', 'bye', 'thanks', 'thank you', 'goodbye'],
    'recommendation_request': ['رشحلي', 'تنصحني', 'اقترحلي', 'أفضل جهاز', 'recommend', 'suggest', 'best device'],
    'product_search': ['عندكم', 'بدور على', 'فيه', 'جهاز', 'do you have', 'looking for', 'search for'],
    'offer': ['خصم', 'عروض', 'أوفر', 'تخفيضات', 'discount', 'offer', 'deal', 'promo'],
    'payment': ['فيزا', 'كاش', 'دفع', 'تقسيط', 'visa', 'cash', 'payment', 'pay'],
    'return': ['أرجع', 'استرداد', 'إرجاع', 'ضمان', 'return', 'refund', 'warranty', 'exchange'],
    'complaint': ['مكسور', 'مش شغال', 'غلط', 'سيئة', 'broken', 'not working', 'wrong', 'terrible'],
    'support': ['إزاي أشغل', 'مش عارف أستخدم', 'error', 'how to use', 'technical support', 'help with device'],
    'feedback': ['ممتاز', 'تجربة رائعة', 'راضي', 'أقيّم', 'excellent', 'great experience', 'satisfied', 'review'],
    'confirmation': ['أجل', 'تمام', 'أوكيه', 'اوكيه', 'موافق', 'صح', 'نعم', 'كويس', 'مظبوط', 'yes', 'okay', 'ok', 'sure', 'confirmed', 'got it', 'sounds good', 'alright'],
}
_BOOST_WEIGHT = 0.08
class IntentClassificationModel:
    _FINETUNED_DIR: str = os.environ.get('INTENT_MODEL_DIR', os.path.join(os.path.dirname(__file__), 'intent_model_finetuned'))
    _BASE_MODEL: str = "UBC-NLP/MARBERTv2"
    def __init__(self) -> None:
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSequenceClassification] = None
        self.device: torch.device = torch.device("cpu")
        self.intent_map: Dict[str, int] = dict(_DEFAULT_INTENT_MAP)
        self.id2intent: Dict[int, str] = {}
        self.num_labels: int = len(_DEFAULT_INTENT_MAP)
        self._rebuild_id2intent()
        self._load_model()
    def _load_model(self) -> None:
        if os.path.isdir(self._FINETUNED_DIR):
            loaded = self._try_load(self._FINETUNED_DIR, label="fine-tuned")
            if loaded:
                self._load_intent_config(self._FINETUNED_DIR)
                return
        logger.warning("Fine-tuned model not found at '%s'. Falling back to base model '%s'.", self._FINETUNED_DIR, self._BASE_MODEL)
        self._try_load(self._BASE_MODEL, label="base")
    def _try_load(self, path_or_name: str, label: str) -> bool:
        try:
            logger.info("Loading %s intent model from: %s", label, path_or_name)
            self.tokenizer = AutoTokenizer.from_pretrained(path_or_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(path_or_name, num_labels=self.num_labels, ignore_mismatched_sizes=True, torch_dtype=torch.float32, low_cpu_mem_usage=True)
            self.model.to(self.device)
            self.model.eval()
            logger.info("✅ %s intent model loaded successfully.", label.capitalize())
            return True
        except Exception as exc:
            logger.error("Failed to load %s intent model: %s", label, exc, exc_info=True)
            self.model, self.tokenizer = None, None
            return False
    def _load_intent_config(self, directory: str) -> None:
        config_path = os.path.join(directory, 'intent_config.json')
        if not os.path.isfile(config_path):
            logger.warning("intent_config.json not found in '%s'. Using default INTENT_MAP.", directory)
            self._rebuild_id2intent()
            return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            loaded_map = cfg.get('intent_map', {})
            if loaded_map:
                self.intent_map = {k: int(v) for k, v in loaded_map.items()}
                self.num_labels = cfg.get('num_labels', len(self.intent_map))
                best_acc = cfg.get('best_val_acc', 'N/A')
                logger.info("intent_config.json loaded: %d intents, best_val_acc=%s", self.num_labels, best_acc)
        except Exception as exc:
            logger.error("Error reading intent_config.json: %s", exc)
        finally:
            self._rebuild_id2intent()
    def _rebuild_id2intent(self) -> None:
        self.id2intent = {v: k for k, v in self.intent_map.items()}
    def predict(self, text: str, last_intent: Optional[str] = None) -> Dict[str, Any]:
        text_lower = text.lower().strip()
        if re.search(r'ord-\d{4}-\d{1,5}', text_lower):
            return self._sure('order_tracking')
        if len(text_lower.split()) <= 6 and any(w in text_lower for w in ['أجل', 'تمام', 'أوكيه', 'اوكيه', 'موافق', 'صح', 'نعم', 'آه', 'أه', 'حلو', 'كويس', 'مظبوط', 'استمر', 'yes', 'okay', 'ok', 'got it', 'sure', 'confirmed', 'sounds good', 'alright']):
            return self._sure('confirmation')
        if any(w in text_lower for w in ['اسمي إيه', 'اسمي ايه', 'مين أنا', 'انا مين', 'تعرف انا مين', 'تعرف اسمي', 'تعرفني', 'فاكرني', 'who am i', "what's my name", 'what is my name', 'do you know my name']):
            return self._sure('memory_check')
        if any(w in text_lower for w in ['ليه رشحت', 'ليه اخترت', 'اشمعنى', 'بناء على ايه', 'why did you recommend', 'why this', 'why recommended']):
            return self._sure('recommendation_reasoning')
        if self.model and self.tokenizer:
            try:
                probs = self._model_probs(text)
            except Exception as exc:
                logger.error("Model inference error: %s", exc)
                probs = self._uniform_probs()
        else:
            probs = self._uniform_probs()
        probs = self._apply_boosts(probs, text_lower)
        if last_intent and last_intent in self.intent_map:
            top_conf = float(np.max(probs))
            if top_conf < 0.45:
                idx = self.intent_map[last_intent]
                probs[idx] = min(1.0, probs[idx] + 0.12)
                probs = probs / probs.sum()
        label_idx = int(np.argmax(probs))
        intent = self.id2intent.get(label_idx, 'inquiry')
        confidence = float(probs[label_idx])
        all_probs = {self.id2intent.get(i, str(i)): float(p) for i, p in enumerate(probs)}
        return {'intent': intent, 'confidence': confidence, 'all_probs': all_probs}
    def _model_probs(self, text: str) -> np.ndarray:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128).to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits.detach().cpu()
        probs = torch.nn.functional.softmax(logits, dim=-1).numpy()[0]
        if len(probs) < self.num_labels:
            probs = np.concatenate([probs, np.zeros(self.num_labels - len(probs))])
        elif len(probs) > self.num_labels:
            probs = probs[:self.num_labels]
        return probs.astype(np.float64)
    def _uniform_probs(self) -> np.ndarray:
        p = np.ones(self.num_labels, dtype=np.float64)
        return p / p.sum()
    def _apply_boosts(self, probs: np.ndarray, text_lower: str) -> np.ndarray:
        boosted = probs.copy()
        for intent_name, keywords in _KEYWORD_BOOSTS.items():
            if intent_name not in self.intent_map:
                continue
            if any(kw in text_lower for kw in keywords):
                idx = self.intent_map[intent_name]
                boosted[idx] = min(1.0, boosted[idx] + _BOOST_WEIGHT)
        total = boosted.sum()
        return boosted / total if total > 0 else boosted
    def _sure(self, intent: str) -> Dict[str, Any]:
        all_probs = {k: 0.0 for k in self.intent_map}
        all_probs[intent] = 1.0
        return {'intent': intent, 'confidence': 1.0, 'all_probs': all_probs}
    def __del__(self) -> None:
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        gc.collect()