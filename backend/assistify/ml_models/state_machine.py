from __future__ import annotations
import re
import logging
from enum import Enum
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .orchestrator import SignalBundle
logger = logging.getLogger(__name__)
_RE_PHONE = re.compile(r"^01[0125][0-9]{8}$")
_CANCEL_WORDS = frozenset([
    "الغاء الطلب", "إلغاء الطلب", "الغي الطلب", "ألغي الطلب",
    "مش عايز", "مش عايزة", "عايز الغاء", "عايزة الغاء", "عايز إلغاء", "عايزة إلغاء",
    "cancel order", "cancel my order", "cancel purchase", "i want to cancel", "please cancel",
])
_ADDRESS_REJECT_TERMS = frozenset([
    "monitor", "thermometer", "oximeter", "nebulizer", "glucose", "pulse",
    "blood pressure", "heart rate", "heating pad", "mask", "infrared", "digital",
    "جهاز", "ترمومتر", "كمامة", "بخاخ", "سكر", "ضغط", "قياس",
    "عايز", "عايزة", "أطلب", "اطلب", "طلب", "شراء", "أشتري", "اشتري",
    "buy", "order", "purchase",
])
_ADDRESS_INDICATORS = frozenset([
    "شارع", "ش ", "حي", "منطقة", "محافظة", "بجوار", "أمام", "خلف",
    "الدور", "شقة", "عمارة", "برج", "مبنى", "بلوك",
    "القاهرة", "الجيزة", "الإسكندرية", "اسكندرية", "المنصورة",
    "الدقهلية", "الشرقية", "المنوفية", "البحيرة", "الغربية",
    "أسيوط", "سوهاج", "قنا", "الأقصر", "أسوان",
    "مدينة نصر", "المعادي", "الزيتون", "شبرا", "هليوبوليس",
    "المهندسين", "الدقي", "العجوزة", "الهرم", "فيصل",
    "street", "avenue", "district", "city", "cairo", "giza",
])
_RE_NAME_AR = re.compile(
    r"(?:اسمي|أنا\s+اسمي|انا\s+اسمي|اسمي\s+هو|معاك|أنا|انا)\s+([\u0600-\u06FF]{2,}(?:\s+[\u0600-\u06FF]{2,})?)"
)
_RE_NAME_EN = re.compile(
    r"(?:my name is|i'm|i am|this is|call me)\s+([a-zA-Z]{2,}(?:\s+[a-zA-Z]{2,})?)", re.I
)
_NAME_BLACKLIST = frozenset([
    "اسمي", "ايه", "إيه", "أنا", "انا", "مين", "هو", "هي", "ده", "دي",
    "بكام", "سعره", "معلومات", "تفاصيل", "عاوزة", "عايزة", "عايز",
    "فين", "مواصفات", "جهاز", "طلب",
    "what", "who", "is", "am", "the", "want", "need", "name",
    "this", "order", "product",
])
class PurchaseState(str, Enum):
    IDLE = "idle"
    AWAITING_NAME = "awaiting_name"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_ADDRESS = "awaiting_address"
    AWAITING_EMAIL = "awaiting_email"
    AWAITING_QUANTITY = "awaiting_quantity"
    READY_TO_ORDER = "ready_to_order"
def extract_name(message: str, language: str) -> Optional[str]:
    tl = message.lower().strip()
    if language == "ar":
        m = _RE_NAME_AR.search(message)
        if m:
            name = m.group(1).strip()
            if name not in _NAME_BLACKLIST and len(name.split()) <= 3:
                return name
    else:
        m = _RE_NAME_EN.search(tl)
        if m:
            name = m.group(1).strip()
            if name.lower() not in _NAME_BLACKLIST and len(name.split()) <= 3:
                return name
    return None
def extract_phone(message: str) -> Optional[str]:
    digits_only = re.sub(r"\s+", "", message.strip())
    digits_only = re.sub(r"^\+?20", "", digits_only)
    if _RE_PHONE.match(digits_only):
        return digits_only
    m = re.search(r"01[0125]\d{8}", re.sub(r"\s+", "", message))
    if m:
        return m.group(0)
    return None
def is_valid_address(text: str) -> bool:
    if len(text.strip()) < 8:
        return False
    tl = text.lower().strip()
    if any(word in tl for word in _ADDRESS_REJECT_TERMS):
        return False
    has_spatial = any(ind in tl for ind in _ADDRESS_INDICATORS)
    if has_spatial:
        return True
    if tl.isdigit():
        return False
    words = tl.split()
    if len(words) >= 2 and not any(w in tl for w in _ADDRESS_REJECT_TERMS):
        return True
    return False
class StateMachine:
    @staticmethod
    def run(bundle: "SignalBundle", conv) -> bool:
        if bundle.purchase_state == PurchaseState.IDLE:
            logger.debug("StateMachine.run called with IDLE state — skipping.")
            return False
        tl = bundle.message.lower().strip()
        if any(word in tl for word in _CANCEL_WORDS):
            return StateMachine._handle_cancel(bundle, conv)
        state = bundle.purchase_state
        if state == PurchaseState.AWAITING_NAME:
            return StateMachine._collect_name(bundle, conv)
        if state == PurchaseState.AWAITING_PHONE:
            return StateMachine._collect_phone(bundle, conv)
        if state == PurchaseState.AWAITING_ADDRESS:
            return StateMachine._collect_address(bundle, conv)
        if state == PurchaseState.AWAITING_EMAIL:
            return StateMachine._collect_email(bundle, conv)
        if state == PurchaseState.AWAITING_QUANTITY:
            return StateMachine._collect_quantity(bundle, conv)
        if state == PurchaseState.READY_TO_ORDER:
            return False
        return False
    @staticmethod
    def start_purchase_flow(bundle: "SignalBundle", conv) -> bool:
        if not bundle.last_product_snapshot:
            if bundle.language == "ar":
                bundle.response = "مش عارف تقصد أي منتج تحديداً 😊 ممكن تقولي اسم المنتج اللي عايزه؟"
            else:
                bundle.response = "I'm not sure which product you mean. Could you mention the product name?"
            bundle.response_conf = 0.95
            return True
        product_name = (
            bundle.last_product_snapshot.get("name")
            or bundle.last_product_snapshot.get("title", "المنتج")
        )
        if not bundle.user_name:
            StateMachine._set_state(bundle, conv, PurchaseState.AWAITING_NAME)
            if bundle.language == "ar":
                bundle.response = f"تمام 👌 هنبدأ طلب {product_name}. محتاجة اسمك الكامل عشان أكمل الطلب."
            else:
                bundle.response = f"Great 👌 Let's start ordering {product_name}. I need your full name to proceed."
            bundle.response_conf = 0.95
            bundle.intent = "purchase_intent"
            return True
        if not bundle.phone:
            StateMachine._set_state(bundle, conv, PurchaseState.AWAITING_PHONE)
            if bundle.language == "ar":
                bundle.response = f"أهلاً {bundle.user_name} 😊 ممكن رقم الموبايل؟"
            else:
                bundle.response = f"Hello {bundle.user_name} 😊 Could you share your phone number?"
            bundle.response_conf = 0.95
            bundle.intent = "purchase_intent"
            return True
        if not bundle.address:
            StateMachine._set_state(bundle, conv, PurchaseState.AWAITING_ADDRESS)
            if bundle.language == "ar":
                bundle.response = "تمام 😊 دلوقتي محتاجة عنوان التوصيل."
            else:
                bundle.response = "Great 😊 Now I need your delivery address."
            bundle.response_conf = 0.95
            bundle.intent = "purchase_intent"
            return True
        if bundle.source == "web" and not bundle.email:
            StateMachine._set_state(bundle, conv, PurchaseState.AWAITING_EMAIL)
            if bundle.language == "ar":
                bundle.response = "محتاجة الإيميل بتاعك عشان نرسل لك تفاصيل الطلب."
            else:
                bundle.response = "I need your email address to send you order details."
            bundle.response_conf = 0.95
            bundle.intent = "purchase_intent"
            return True
        if not bundle.quantity:
            StateMachine._set_state(bundle, conv, PurchaseState.AWAITING_QUANTITY)
            if bundle.language == "ar":
                bundle.response = "تمام 😊 كام قطعة تحبي تطلبي؟"
            else:
                bundle.response = "Great 😊 How many units would you like to order?"
            bundle.response_conf = 0.95
            bundle.intent = "purchase_intent"
            return True
        StateMachine._set_state(bundle, conv, PurchaseState.READY_TO_ORDER)
        return False
    @staticmethod
    def _collect_name(bundle: "SignalBundle", conv) -> bool:
        if bundle.user_name:
            name = bundle.user_name
        else:
            name = extract_name(bundle.message, bundle.language)
            if not name:
                tl = bundle.message.strip()
                if (
                    len(tl) >= 2
                    and not tl.isdigit()
                    and not extract_phone(tl)
                    and not any(w in tl.lower() for w in _ADDRESS_REJECT_TERMS)
                    and len(tl.split()) <= 4
                ):
                    name = tl
        if name:
            bundle.user_name = name
            bundle.intent = "introduce_name"
            bundle.intent_conf = 1.0
            if conv:
                conv.user_name = name
                conv.purchase_state = PurchaseState.AWAITING_PHONE.value
                try:
                    conv.save(update_fields=["user_name", "purchase_state"])
                except Exception as exc:
                    logger.warning("Could not save user_name: %s", exc)
            bundle.purchase_state = PurchaseState.AWAITING_PHONE
            if bundle.phone:
                return StateMachine._collect_phone(bundle, conv)
            if bundle.language == "ar":
                bundle.response = f"أهلاً {name} 😊 ممكن رقم الموبايل؟"
            else:
                bundle.response = f"Nice to meet you, {name}! Could you share your phone number?"
            bundle.response_conf = 0.95
            return True
        if bundle.language == "ar":
            bundle.response = "معنديش اسمك لسه 😊 ممكن تقولي اسمك الكامل؟"
        else:
            bundle.response = "Could you please share your full name?"
        bundle.response_conf = 0.95
        return True
    @staticmethod
    def _collect_phone(bundle: "SignalBundle", conv) -> bool:
        phone = bundle.phone or extract_phone(bundle.message)
        if phone:
            bundle.phone = phone
            bundle.intent = "provide_phone"
            bundle.intent_conf = 1.0
            if conv:
                conv.phone = phone
                conv.purchase_state = PurchaseState.AWAITING_ADDRESS.value
                try:
                    conv.save(update_fields=["phone", "purchase_state"])
                except Exception as exc:
                    logger.warning("Could not save phone: %s", exc)
            bundle.purchase_state = PurchaseState.AWAITING_ADDRESS
            if bundle.address:
                return StateMachine._collect_address(bundle, conv)
            if bundle.language == "ar":
                bundle.response = "تمام 😊 دلوقتي محتاجة عنوان التوصيل."
            else:
                bundle.response = "Got it! Now I need your delivery address."
            bundle.response_conf = 0.95
            return True
        if bundle.language == "ar":
            bundle.response = "الرقم ده مش صح 😊 ممكن تبعتلي رقم مصري صحيح (مثال: 01012345678)؟"
        else:
            bundle.response = "That doesn't look like a valid Egyptian number. Please share a valid phone (e.g. 01012345678)."
        bundle.response_conf = 0.95
        return True
    @staticmethod
    def _collect_address(bundle: "SignalBundle", conv) -> bool:
        if bundle.address and is_valid_address(bundle.address):
            candidate = bundle.address
        else:
            candidate = bundle.message.strip()
        if is_valid_address(candidate):
            bundle.address = candidate
            bundle.intent = "provide_address"
            bundle.intent_conf = 1.0
            if conv:
                conv.address = candidate
                conv.purchase_state = PurchaseState.AWAITING_QUANTITY.value
                try:
                    conv.save(update_fields=["address", "purchase_state"])
                except Exception as exc:
                    logger.warning("Could not save address: %s", exc)
            bundle.purchase_state = PurchaseState.AWAITING_EMAIL if bundle.source == "web" else PurchaseState.AWAITING_QUANTITY
            if bundle.source == "web" and not bundle.email:
                return StateMachine._collect_email(bundle, conv)
            if bundle.quantity:
                return StateMachine._collect_quantity(bundle, conv)
            if bundle.language == "ar":
                bundle.response = "تمام 😊 كام قطعة تحبي تطلبي؟"
            else:
                bundle.response = "Got it! How many units would you like to order?"
            bundle.response_conf = 0.95
            return True
        if bundle.language == "ar":
            bundle.response = "ممكن تبعتلي عنوان تفصيلي أكتر؟ (مثال: القاهرة - مدينة نصر - شارع عباس)"
        else:
            bundle.response = "Could you share a more detailed address? (e.g. Cairo, Nasr City, Abbas St.)"
        bundle.response_conf = 0.95
        return True
    @staticmethod
    def _collect_email(bundle: "SignalBundle", conv) -> bool:
        email = bundle.email
        if not email:
            import re
            tl = bundle.message.strip()
            match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", tl)
            if match:
                email = match.group(0)
        if email:
            bundle.email = email
            bundle.intent = "provide_email"
            bundle.intent_conf = 1.0
            if conv:
                conv.email = email
                conv.purchase_state = PurchaseState.AWAITING_QUANTITY.value
                try:
                    conv.save(update_fields=["email", "purchase_state"])
                except Exception as exc:
                    logger.warning("Could not save email: %s", exc)
            bundle.purchase_state = PurchaseState.AWAITING_QUANTITY
            if bundle.quantity:
                return StateMachine._collect_quantity(bundle, conv)
            if bundle.language == "ar":
                bundle.response = "تمام 😊 كام قطعة تحبي تطلبي؟"
            else:
                bundle.response = "Got it! How many units would you like to order?"
            bundle.response_conf = 0.95
            return True
        if bundle.language == "ar":
            bundle.response = "ده مش شكل إيميل صحيح 😊 ممكن تبعت إيميلك؟ (مثال: email@example.com)"
        else:
            bundle.response = "That doesn't look like a valid email. Please provide your email address."
        bundle.response_conf = 0.95
        return True
    @staticmethod
    def _collect_quantity(bundle: "SignalBundle", conv) -> bool:
        qty = bundle.quantity
        tl = bundle.message.strip()
        if not qty and tl.isdigit():
            qty = int(tl)
            if 1 <= qty <= 99:
                bundle.quantity = qty
        if qty and 1 <= qty <= 99:
            bundle.quantity = qty
            bundle.intent = "provide_quantity"
            bundle.intent_conf = 1.0
            if conv:
                conv.quantity = qty
                conv.purchase_state = PurchaseState.READY_TO_ORDER.value
                try:
                    conv.save(update_fields=["quantity", "purchase_state"])
                except Exception as exc:
                    logger.warning("Could not save quantity: %s", exc)
            bundle.purchase_state = PurchaseState.READY_TO_ORDER
            return False
        if bundle.language == "ar":
            bundle.response = "ممكن تبعتلي الكمية كرقم؟ (مثال: 1 أو 2)"
        else:
            bundle.response = "Could you share the quantity as a number? (e.g. 1 or 2)"
        bundle.response_conf = 0.95
        return True
    @staticmethod
    def _handle_cancel(bundle: "SignalBundle", conv) -> bool:
        bundle.intent = "cancel_purchase"
        bundle.intent_conf = 1.0
        StateMachine._set_state(bundle, conv, PurchaseState.IDLE)
        if bundle.language == "ar":
            bundle.response = "تم إلغاء الطلب 😊 أقدر أساعدك في أي حاجة تانية؟"
        else:
            bundle.response = "Order cancelled. How else can I help you?"
        bundle.response_conf = 0.95
        return True
    @staticmethod
    def _set_state(bundle: "SignalBundle", conv, state: PurchaseState) -> None:
        bundle.purchase_state = state
        if conv:
            conv.purchase_state = state.value
            try:
                conv.save(update_fields=["purchase_state"])
            except Exception as exc:
                logger.warning("Could not save purchase_state: %s", exc)