from rest_framework import serializers
from .models import Product, ProductBenefit, Offer
class ProductBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBenefit
        fields = ("id", "text", "order")
class RelatedProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "currency", "emoji", "image_url", "description", "category", "color", "sizes")
class ProductSerializer(serializers.ModelSerializer):
    benefits = ProductBenefitSerializer(many=True, read_only=True)
    related_products = RelatedProductSerializer(many=True, read_only=True)
    offer = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "category",
            "category_display",
            "gender",
            "description",
            "price",
            "currency",
            "color",
            "sizes",
            "emoji",
            "image_url",
            "is_active",
            "benefits",
            "related_products",
            "offer",
            "created_at",
            "updated_at",
        )
    def get_offer(self, obj):
        try:
            offer = obj.offer
            if offer.is_active:
                return OfferSerializer(offer).data
        except Offer.DoesNotExist:
            pass
        return None
class ProductWriteSerializer(serializers.ModelSerializer):
    benefits = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    related_product_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Product.objects.all(), write_only=True, required=False, source="related_products"
    )
    class Meta:
        model = Product
        fields = (
            "id", "name", "category", "description", "price", "currency",
            "color", "sizes", "emoji", "image_url", "is_active", "benefits", "related_product_ids",
        )
    def create(self, validated_data):
        benefits_data = validated_data.pop("benefits", [])
        related = validated_data.pop("related_products", [])
        product = Product.objects.create(**validated_data)
        product.related_products.set(related)
        for i, text in enumerate(benefits_data):
            ProductBenefit.objects.create(product=product, text=text, order=i)
        return product
    def update(self, instance, validated_data):
        benefits_data = validated_data.pop("benefits", None)
        related = validated_data.pop("related_products", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if related is not None:
            instance.related_products.set(related)
        if benefits_data is not None:
            instance.benefits.all().delete()
            for i, text in enumerate(benefits_data):
                ProductBenefit.objects.create(product=instance, text=text, order=i)
        return instance
class OfferSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_emoji = serializers.CharField(source="product.emoji", read_only=True)
    product_image = serializers.CharField(source="product.image_url", read_only=True)
    original_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    class Meta:
        model = Offer
        fields = (
            "id",
            "product",
            "product_name",
            "product_emoji",
            "product_image",
            "original_price",
            "discount_percent",
            "discounted_price",
            "is_active",
            "valid_until",
        )