from django.db import models
class Product(models.Model):
    class CategoryChoices(models.TextChoices):
        SUITS = 'suits', 'Suits & Tuxedos'
        DRESSES = 'dresses', 'Evening Dresses & Gowns'
        SHIRTS = 'shirts', 'Shirts & Blouses'
        FOOTWEAR = 'footwear', 'Formal Footwear'
        ACCESSORIES = 'accessories', 'Accessories'
        OUTERWEAR = 'outerwear', 'Coats & Blazers'

    class GenderChoices(models.TextChoices):
        MEN = 'men', "Men"
        WOMEN = 'women', "Women"
        UNISEX = 'unisex', "Unisex"

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CategoryChoices.choices, default=CategoryChoices.ACCESSORIES)
    gender = models.CharField(max_length=10, choices=GenderChoices.choices, default=GenderChoices.UNISEX)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="EGP")
    color = models.CharField(max_length=50, blank=True, help_text="Primary color of the item, e.g. 'Navy Blue'")
    sizes = models.JSONField(default=list, blank=True, help_text="List of available sizes, e.g. ['M','L','XL'] or ['42','43']")
    image_url = models.URLField(max_length=500, blank=True, help_text="URL of the product image")
    emoji = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    features = models.JSONField(default=list, blank=True, help_text="List of product features")
    suitable_for = models.JSONField(default=list, blank=True, help_text="List of user types or conditions this is suitable for")
    use_cases = models.JSONField(default=list, blank=True, help_text="List of scenarios where this product is used")
    related_products = models.ManyToManyField(
        "self", blank=True, symmetrical=True, related_name="related_to"
    )
    class Meta:
        db_table = "products"
        ordering = ["id"]
    def __str__(self):
        return self.name
class ProductBenefit(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="benefits")
    text = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)
    class Meta:
        db_table = "product_benefits"
        ordering = ["order"]
    def __str__(self):
        return f"{self.product.name}: {self.text}"
class Offer(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="offer")
    discount_percent = models.PositiveSmallIntegerField()
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)
    class Meta:
        db_table = "offers"
    def __str__(self):
        return f"{self.product.name} — {self.discount_percent}% off"