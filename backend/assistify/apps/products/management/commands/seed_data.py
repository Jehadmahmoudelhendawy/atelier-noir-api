import random
from django.core.management.base import BaseCommand
from assistify.apps.products.models import Product, ProductBenefit, Offer
from assistify.apps.users.models import User
from assistify.apps.orders.models import Order, OrderItem
PRODUCTS = [
    {
        "id": 1,
        "name": "Classic Two-Piece Suit",
        "category": "suits",
        "description": "Tailored wool-blend suit with a modern slim cut",
        "price": 6499,
        "emoji": "🤵",
        "benefits": [
            "Premium Italian wool-blend fabric",
            "Half-canvas construction for a sharp drape",
            "Slim, contemporary silhouette",
            "Functional surgeon's cuffs",
            "Complimentary in-house alterations",
        ],
        "related_ids": [2, 5],
    },
    {
        "id": 2,
        "name": "Black Tie Tuxedo",
        "category": "suits",
        "description": "Satin-lapel tuxedo for black-tie occasions",
        "price": 8999,
        "emoji": "🎩",
        "benefits": [
            "Grosgrain satin peak lapels",
            "Midnight-black super 120s wool",
            "Tailored evening fit",
            "Matching satin trouser stripe",
            "Includes garment bag",
        ],
        "related_ids": [1, 9],
    },
    {
        "id": 3,
        "name": "Egyptian Cotton Dress Shirt",
        "category": "shirts",
        "description": "Crisp formal shirt in premium Egyptian cotton",
        "price": 1299,
        "emoji": "👔",
        "benefits": [
            "100% Egyptian cotton",
            "Classic point collar",
            "Mother-of-pearl buttons",
            "Wrinkle-resistant weave",
            "Tailored fit",
        ],
        "related_ids": [1, 5],
    },
    {
        "id": 4,
        "name": "Leather Oxford Shoes",
        "category": "footwear",
        "description": "Hand-finished full-grain calfskin oxfords",
        "price": 3299,
        "emoji": "👞",
        "benefits": [
            "Full-grain Italian calfskin",
            "Goodyear-welted leather sole",
            "Closed lacing for a formal finish",
            "Cushioned leather insole",
            "Available in black & oxblood",
        ],
        "related_ids": [1, 6],
    },
    {
        "id": 5,
        "name": "Silk Tie & Cufflink Set",
        "category": "accessories",
        "description": "Woven silk tie with matching cufflinks",
        "price": 1299,
        "emoji": "👔",
        "benefits": [
            "Woven jacquard silk tie",
            "Sterling-finish cufflinks",
            "Presented in a gift box",
            "Timeless patterns",
            "The perfect finishing touch",
        ],
        "related_ids": [1, 3],
    },
    {
        "id": 6,
        "name": "Tailored Blazer",
        "category": "outerwear",
        "description": "Structured single-breasted wool-blend blazer",
        "price": 4499,
        "emoji": "🧥",
        "benefits": [
            "Structured shoulder with light padding",
            "Notch lapel, two-button front",
            "Breathable wool-blend cloth",
            "Versatile day-to-evening piece",
            "Side vents for ease of movement",
        ],
        "related_ids": [3, 4],
    },
    {
        "id": 7,
        "name": "Silk Evening Gown",
        "category": "dresses",
        "description": "Floor-length silk gown with a draped neckline",
        "price": 7499,
        "emoji": "👗",
        "benefits": [
            "100% pure mulberry silk",
            "Bias-cut for a fluid silhouette",
            "Concealed back zip",
            "Made-to-measure available",
            "Hand-finished hem",
        ],
        "related_ids": [8, 10],
    },
    {
        "id": 8,
        "name": "Satin Cocktail Dress",
        "category": "dresses",
        "description": "Knee-length satin cocktail dress",
        "price": 4299,
        "emoji": "💃",
        "benefits": [
            "Lustrous satin fabric",
            "Flattering contemporary cut",
            "Concealed zip closure",
            "Fully lined",
            "Available in multiple shades",
        ],
        "related_ids": [7, 10],
    },
    {
        "id": 9,
        "name": "Wool Overcoat",
        "category": "outerwear",
        "description": "Long wool overcoat for formal winter wear",
        "price": 6999,
        "emoji": "🧥",
        "benefits": [
            "Warm premium wool",
            "Classic full-length cut",
            "Elegant inner lining",
            "Layers neatly over a suit",
            "Timeless silhouette",
        ],
        "related_ids": [1, 2],
    },
    {
        "id": 10,
        "name": "Satin Heeled Sandals",
        "category": "footwear",
        "description": "Elegant satin sandals with a slim heel",
        "price": 2499,
        "emoji": "👠",
        "benefits": [
            "Refined satin upper",
            "Comfortable slim heel",
            "Cushioned footbed",
            "Perfect for evening wear",
            "Pairs with gowns and dresses",
        ],
        "related_ids": [7, 8],
    },
]
OFFERS = [
    {"product_id": 5, "discount_percent": 20, "discounted_price": 1039},
    {"product_id": 6, "discount_percent": 15, "discounted_price": 3824},
    {"product_id": 4, "discount_percent": 25, "discounted_price": 2474},
]
class Command(BaseCommand):
    help = "Seed database with initial Assistify products, offers, and user interactions for LightFM"
    def handle(self, *args, **options):
        self.stdout.write("Seeding products...")
        id_map = {}
        all_products = []
        for data in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=data["name"],
                defaults={
                    "category": data.get("category", "accessories"),
                    "description": data["description"],
                    "price": data["price"],
                    "emoji": data["emoji"],
                    "color": data.get("color", ""),
                    "sizes": data.get("sizes", []),
                    "currency": "EGP",
                },
            )
            id_map[data["id"]] = product
            all_products.append(product)
            if created:
                for i, text in enumerate(data["benefits"]):
                    ProductBenefit.objects.create(product=product, text=text, order=i)
                self.stdout.write(self.style.SUCCESS(f"  Created: {product.name}"))
            else:
                self.stdout.write(f"  Exists:  {product.name}")
        for data in PRODUCTS:
            product = id_map[data["id"]]
            related = [id_map[rid] for rid in data["related_ids"] if rid in id_map]
            product.related_products.set(related)
        self.stdout.write("Seeding offers...")
        for offer_data in OFFERS:
            product = id_map.get(offer_data["product_id"])
            if product:
                offer, created = Offer.objects.get_or_create(
                    product=product,
                    defaults={
                        "discount_percent": offer_data["discount_percent"],
                        "discounted_price": offer_data["discounted_price"],
                    },
                )
                status = "Created" if created else "Exists"
                self.stdout.write(
                    self.style.SUCCESS(f"  {status}: {product.name} — {offer.discount_percent}% off")
                )
        self.stdout.write("Seeding user interactions for LightFM...")
        users = []
        for i in range(1, 6):
            username = f'user_{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com'}
            )
            users.append(user)
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'  Created user: {username}')
        if users and all_products:
            for user in users:
                num_purchases = random.randint(2, 4)
                purchased_products = random.sample(all_products, num_purchases)
                order = Order.objects.create(
                    user=user, 
                    customer_email=user.email,
                    subtotal=0,
                    total=0,
                    shipping_fee=50
                )
                total_subtotal = 0
                for product in purchased_products:
                    OrderItem.objects.create(
                        order=order, 
                        product=product, 
                        product_name=product.name,
                        product_emoji=product.emoji,
                        unit_price=product.price,
                        quantity=1
                    )
                    total_subtotal += product.price
                order.subtotal = total_subtotal
                order.total = total_subtotal + order.shipping_fee
                order.save()
                self.stdout.write(f'  User {user.username} interacted with {num_purchases} products.')
        self.stdout.write(self.style.SUCCESS("\n✅ Seeding complete! LightFM now has data to learn from."))