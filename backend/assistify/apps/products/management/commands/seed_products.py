import re
from decimal import Decimal

from django.core.management.base import BaseCommand
from assistify.apps.products.models import Product, Offer

# ----- Size scales -----
SIZES_SUIT = ["46", "48", "50", "52", "54", "56"]
SIZES_SHIRT = ["S", "M", "L", "XL", "XXL"]
SIZES_DRESS = ["XS", "S", "M", "L", "XL"]
SIZES_SHOE_M = ["40", "41", "42", "43", "44", "45"]
SIZES_SHOE_W = ["36", "37", "38", "39", "40", "41"]
ONE_SIZE = ["One Size"]

# ----- Catalog definition -----
# Each "line" generates one Product per color (name carries the color so search
# by color — e.g. "blue tie" — works on both name and the dedicated color field).
LINES = [
    {
        "name_en": "Two-Piece Suit", "name_ar": "بدلة قطعتين",
        "category": "suits", "emoji": "🤵", "price": 6499, "sizes": SIZES_SUIT,
        "desc_ar": "بدلة رجالي قطعتين من الصوف بقصة سليم أنيقة تناسب العمل والمناسبات الرسمية",
        "features_ar": ["خامة صوف فاخرة", "قصة سليم عصرية", "بطانة مريحة", "تفصيل نصف كانفاس"],
        "colors": [("Navy Blue", "كحلي"), ("Charcoal", "رمادي غامق"), ("Black", "أسود"),
                   ("Light Grey", "رمادي فاتح"), ("Beige", "بيج")],
    },
    {
        "name_en": "Tuxedo", "name_ar": "توكسيدو",
        "category": "suits", "emoji": "🎩", "price": 8999, "sizes": SIZES_SUIT,
        "desc_ar": "توكسيدو رسمي بياقة ساتان لامعة مصمم لمناسبات البلاك تاي والحفلات الكبرى",
        "features_ar": ["ياقة ساتان جروجران", "صوف سوبر 120s", "قصة مسائية مفصلة", "شريط ساتان على البنطلون"],
        "colors": [("Black", "أسود"), ("Midnight Blue", "أزرق ليلي")],
    },
    {
        "name_en": "Three-Piece Suit", "name_ar": "بدلة ثري بيس",
        "category": "suits", "emoji": "🕴️", "price": 7499, "sizes": SIZES_SUIT,
        "desc_ar": "بدلة ثلاث قطع تشمل الجاكيت والصديري والبنطلون لإطلالة كاملة الأناقة",
        "features_ar": ["ثلاث قطع متناسقة", "صديري بقصة مثالية", "قماش مقاوم للتجعد", "فتحتان خلفيتان"],
        "colors": [("Navy Blue", "كحلي"), ("Charcoal", "رمادي غامق")],
    },
    {
        "name_en": "Tailored Blazer", "name_ar": "بليزر مفصل",
        "category": "outerwear", "emoji": "🧥", "price": 4499, "sizes": SIZES_SUIT,
        "desc_ar": "بليزر مفصل بصف أزرار واحد وقصة منظمة ينتقل بك من النهار للمساء بأناقة",
        "features_ar": ["أكتاف منظمة بحشوة خفيفة", "ياقة نوتش", "قماش صوف يسمح بالتهوية", "فتحتان جانبيتان"],
        "colors": [("Navy Blue", "كحلي"), ("Black", "أسود"), ("Grey", "رمادي"), ("Burgundy", "نبيتي")],
    },
    {
        "name_en": "Wool Overcoat", "name_ar": "بالطو صوف",
        "category": "outerwear", "emoji": "🧥", "price": 6999, "sizes": SIZES_SUIT,
        "desc_ar": "بالطو طويل من الصوف الفاخر بقصة كلاسيكية يضفي الدفء والرقي فوق البدلة",
        "features_ar": ["صوف فاخر دافئ", "قصة طويلة كلاسيكية", "بطانة داخلية أنيقة", "يناسب فوق البدلة"],
        "colors": [("Camel", "جملي"), ("Charcoal", "رمادي غامق"), ("Black", "أسود")],
    },
    {
        "name_en": "Dress Shirt", "name_ar": "قميص رسمي",
        "category": "shirts", "emoji": "👔", "price": 1299, "sizes": SIZES_SHIRT,
        "desc_ar": "قميص رسمي من القطن المصري الفاخر بقصة مثالية وياقة كلاسيكية",
        "features_ar": ["قطن مصري 100%", "ياقة كلاسيكية متينة", "أزرار صدف", "قابل للكي بسهولة"],
        "colors": [("White", "أبيض"), ("Light Blue", "أزرق فاتح"), ("Black", "أسود"),
                   ("Pink", "وردي"), ("Lavender", "لافندر")],
    },
    {
        "name_en": "Silk Blouse", "name_ar": "بلوزة حرير",
        "category": "shirts", "emoji": "👚", "price": 1899, "sizes": SIZES_DRESS,
        "desc_ar": "بلوزة نسائية رسمية من الحرير الناعم بتصميم راقٍ يجمع بين الأناقة والراحة",
        "features_ar": ["حرير ناعم فاخر", "قصة انسيابية", "تفاصيل أنيقة", "سهلة التنسيق"],
        "colors": [("White", "أبيض"), ("Black", "أسود"), ("Champagne", "شامبني"), ("Burgundy", "نبيتي")],
    },
    {
        "name_en": "Evening Gown", "name_ar": "فستان سهرة",
        "category": "dresses", "emoji": "👗", "price": 7499, "sizes": SIZES_DRESS,
        "desc_ar": "فستان سهرة طويل من الحرير بقصة انسيابية مثالي للمناسبات المسائية الراقية",
        "features_ar": ["حرير طبيعي فاخر", "قصة باياس انسيابية", "سحاب خلفي مخفي", "تفصيل حسب المقاس متاح"],
        "colors": [("Black", "أسود"), ("Red", "أحمر"), ("Emerald", "أخضر زمردي"),
                   ("Navy Blue", "كحلي"), ("Burgundy", "نبيتي")],
    },
    {
        "name_en": "Cocktail Dress", "name_ar": "فستان كوكتيل",
        "category": "dresses", "emoji": "💃", "price": 4299, "sizes": SIZES_DRESS,
        "desc_ar": "فستان كوكتيل أنيق من الساتان بطول الركبة بتصميم عصري يناسب السهرات",
        "features_ar": ["خامة ساتان فاخرة", "طول مثالي للكوكتيل", "قصة عصرية", "بطانة كاملة"],
        "colors": [("Black", "أسود"), ("Red", "أحمر"), ("Royal Blue", "أزرق ملكي")],
    },
    {
        "name_en": "Oxford Shoes", "name_ar": "حذاء أوكسفورد",
        "category": "footwear", "emoji": "👞", "price": 3299, "sizes": SIZES_SHOE_M,
        "desc_ar": "حذاء أوكسفورد رجالي من الجلد الطبيعي الكامل بخياطة جودير ويلت وأناقة كلاسيكية",
        "features_ar": ["جلد طبيعي إيطالي كامل", "نعل جلد بخياطة جودير ويلت", "رباط مغلق رسمي", "نعلة داخلية مبطنة"],
        "colors": [("Black", "أسود"), ("Oxblood", "أحمر داكن"), ("Brown", "بني")],
    },
    {
        "name_en": "Heeled Sandals", "name_ar": "صندل كعب",
        "category": "footwear", "emoji": "👠", "price": 2499, "sizes": SIZES_SHOE_W,
        "desc_ar": "صندل نسائي بكعب رفيع من الساتان يكمل إطلالة السهرة بثقة وأناقة",
        "features_ar": ["خامة ساتان راقية", "كعب رفيع مريح", "نعلة ناعمة", "تصميم مناسب للسهرات"],
        "colors": [("Black", "أسود"), ("Nude", "بيج فاتح"), ("Gold", "ذهبي"), ("Silver", "فضي")],
    },
    {
        "name_en": "Silk Tie", "name_ar": "كرافتة حرير",
        "category": "accessories", "emoji": "👔", "price": 549, "sizes": ONE_SIZE,
        "desc_ar": "كرافتة من الحرير المنسوج تقدم اللمسة الأخيرة المثالية لأي إطلالة رسمية",
        "features_ar": ["حرير جاكار منسوج", "عرض كلاسيكي 8 سم", "تصاميم خالدة", "تأتي في علبة أنيقة"],
        "colors": [("Navy Blue", "كحلي"), ("Royal Blue", "أزرق ملكي"), ("Sky Blue", "أزرق سماوي"),
                   ("Burgundy", "نبيتي"), ("Black", "أسود"), ("Silver", "فضي"), ("Emerald", "أخضر زمردي")],
    },
    {
        "name_en": "Bow Tie", "name_ar": "بابيون",
        "category": "accessories", "emoji": "🎀", "price": 449, "sizes": ONE_SIZE,
        "desc_ar": "بابيون حرير قابل للتعديل مثالي مع التوكسيدو ومناسبات البلاك تاي",
        "features_ar": ["حرير فاخر", "رقبة قابلة للتعديل", "عقدة جاهزة أنيقة", "يأتي في علبة هدية"],
        "colors": [("Black", "أسود"), ("Navy Blue", "كحلي")],
    },
    {
        "name_en": "Cufflinks", "name_ar": "أزرار أكمام",
        "category": "accessories", "emoji": "🔗", "price": 799, "sizes": ONE_SIZE,
        "desc_ar": "أزرار أكمام راقية تضيف لمسة من الفخامة لإطلالة القميص الرسمي",
        "features_ar": ["معدن مصقول عالي الجودة", "تصميم كلاسيكي", "إغلاق محوري ثابت", "علبة هدية فاخرة"],
        "colors": [("Silver", "فضي"), ("Gold", "ذهبي"), ("Onyx Black", "أسود أونيكس")],
    },
    {
        "name_en": "Leather Belt", "name_ar": "حزام جلد",
        "category": "accessories", "emoji": "🪢", "price": 899, "sizes": ["90", "95", "100", "105", "110"],
        "desc_ar": "حزام رجالي من الجلد الطبيعي بإبزيم معدني أنيق يكمل الإطلالة الرسمية",
        "features_ar": ["جلد طبيعي فاخر", "إبزيم معدني أنيق", "متين وطويل الأمد", "خياطة دقيقة"],
        "colors": [("Black", "أسود"), ("Brown", "بني")],
    },
    {
        "name_en": "Pocket Square", "name_ar": "منديل جيب",
        "category": "accessories", "emoji": "🤍", "price": 299, "sizes": ONE_SIZE,
        "desc_ar": "منديل جيب من الحرير يضيف لمسة مميزة وأنيقة لجيب الجاكيت",
        "features_ar": ["حرير ناعم", "حواف مخيطة يدوياً", "مقاس كلاسيكي", "يكمل الكرافتة"],
        "colors": [("White", "أبيض"), ("Navy Blue", "كحلي"), ("Burgundy", "نبيتي")],
    },
    {
        "name_en": "Cashmere Scarf", "name_ar": "إيشارب كشمير",
        "category": "accessories", "emoji": "🧣", "price": 1599, "sizes": ONE_SIZE,
        "desc_ar": "إيشارب فاخر من الكشمير الناعم يمنح الدفء والأناقة لإطلالات الشتاء الرسمية",
        "features_ar": ["كشمير ناعم 100%", "خفيف ودافئ", "ألوان كلاسيكية", "لمسة فاخرة"],
        "colors": [("Grey", "رمادي"), ("Camel", "جملي"), ("Black", "أسود"), ("Burgundy", "نبيتي")],
    },
]

# Descriptive noun per base type — used to build AI image-generation prompts
# (see the `generate_product_images` management command).
PROMPT_NOUNS = {
    "Two-Piece Suit": "men's two-piece formal suit",
    "Tuxedo": "men's tuxedo with satin lapels",
    "Three-Piece Suit": "men's three-piece formal suit with a waistcoat",
    "Tailored Blazer": "men's tailored blazer jacket",
    "Wool Overcoat": "men's long wool overcoat",
    "Dress Shirt": "men's formal dress shirt",
    "Silk Blouse": "women's elegant silk blouse",
    "Evening Gown": "women's long elegant evening gown",
    "Cocktail Dress": "women's knee-length cocktail dress",
    "Oxford Shoes": "a pair of men's leather oxford dress shoes",
    "Heeled Sandals": "a pair of women's elegant high-heeled sandals",
    "Silk Tie": "a men's silk necktie",
    "Bow Tie": "a men's bow tie",
    "Cufflinks": "a pair of elegant cufflinks",
    "Leather Belt": "a men's leather dress belt",
    "Pocket Square": "a folded silk pocket square",
    "Cashmere Scarf": "a soft cashmere scarf",
}


# Gender per base type — so the assistant never mixes men's and women's pieces.
GENDER_BY_TYPE = {
    "Two-Piece Suit": "men",
    "Tuxedo": "men",
    "Three-Piece Suit": "men",
    "Tailored Blazer": "men",
    "Wool Overcoat": "men",
    "Dress Shirt": "men",
    "Silk Blouse": "women",
    "Evening Gown": "women",
    "Cocktail Dress": "women",
    "Oxford Shoes": "men",
    "Heeled Sandals": "women",
    "Silk Tie": "men",
    "Bow Tie": "men",
    "Cufflinks": "men",
    "Leather Belt": "men",
    "Pocket Square": "men",
    "Cashmere Scarf": "unisex",
}


def product_slug(name_en, color_en):
    """Stable filename slug shared by the seed and the image generator."""
    return re.sub(r"[^a-z0-9]+", "-", f"{color_en}-{name_en}".lower()).strip("-")


def build_image_url(name_en, color_en, lock=None):
    """Relative path to the product's static image (served by the frontend).
    The image is produced by `generate_product_images`; if missing, the
    frontend falls back to an elegant color panel."""
    return f"/products/{product_slug(name_en, color_en)}.jpg"


# Products to put on sale: (name_en substring, color_en, discount_percent)
OFFER_SPECS = [
    ("Silk Tie", "Royal Blue", 20),
    ("Tailored Blazer", "Burgundy", 15),
    ("Oxford Shoes", "Oxblood", 25),
    ("Cocktail Dress", "Red", 20),
    ("Cashmere Scarf", "Camel", 15),
]


class Command(BaseCommand):
    help = "Seeds the database with a rich, multi-color formal-wear catalog"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing existing products...")
        Product.objects.all().delete()

        created = 0
        for line in LINES:
            for color_en, color_ar in line["colors"]:
                created += 1
                name = f"{color_en} {line['name_en']} / {line['name_ar']} {color_ar}"
                Product.objects.create(
                    name=name,
                    category=line["category"],
                    gender=GENDER_BY_TYPE.get(line["name_en"], "unisex"),
                    color=color_en,
                    sizes=line["sizes"],
                    description=f"{line['desc_ar']} - اللون {color_ar}.",
                    price=Decimal(str(line["price"])),
                    emoji=line["emoji"],
                    image_url=build_image_url(line["name_en"], color_en, created),
                    features=line["features_ar"],
                    is_active=True,
                )

        self.stdout.write(f"Created {created} products. Building outfit (طقم) links...")
        self._link_outfits()

        self.stdout.write("Seeding offers...")
        self._seed_offers()

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created} formal-wear products with colors, sizes, outfit links, and offers!"))

    def _link_outfits(self):
        def one(name_sub, color=None):
            qs = Product.objects.filter(name__icontains=name_sub)
            if color:
                qs = qs.filter(color=color)
            return qs.first()

        shirt_white = one("Dress Shirt", "White")
        tie_navy = one("Silk Tie", "Navy Blue")
        tie_burgundy = one("Silk Tie", "Burgundy")
        oxford_black = one("Oxford Shoes", "Black")
        belt_black = one("Leather Belt", "Black")
        cufflinks_silver = one("Cufflinks", "Silver")
        pocket_white = one("Pocket Square", "White")
        heels_black = one("Heeled Sandals", "Black")
        heels_gold = one("Heeled Sandals", "Gold")
        scarf_black = one("Cashmere Scarf", "Black")

        men_set = [p for p in [shirt_white, tie_navy, tie_burgundy, oxford_black, belt_black, cufflinks_silver, pocket_white] if p]
        women_set = [p for p in [heels_black, heels_gold, scarf_black] if p]

        # Suits & tuxedos & three-piece -> full men's outfit
        for suit in Product.objects.filter(category="suits"):
            suit.related_products.add(*men_set)
        # Blazers & overcoats -> shirt, tie, shoes, belt
        for outer in Product.objects.filter(category="outerwear"):
            outer.related_products.add(*[p for p in [shirt_white, tie_navy, oxford_black, belt_black] if p])
        # Gowns & cocktail dresses -> heels + scarf
        for dress in Product.objects.filter(category="dresses"):
            dress.related_products.add(*women_set)

    def _seed_offers(self):
        for name_sub, color_en, pct in OFFER_SPECS:
            product = Product.objects.filter(name__icontains=name_sub, color=color_en).first()
            if not product:
                continue
            discounted = (product.price * (Decimal(100) - Decimal(pct)) / Decimal(100)).quantize(Decimal("1"))
            Offer.objects.update_or_create(
                product=product,
                defaults={"discount_percent": pct, "discounted_price": discounted, "is_active": True},
            )
