from django.contrib import admin
from .models import Product, ProductBenefit, Offer
class BenefitInline(admin.TabularInline):
    model = ProductBenefit
    extra = 1
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "currency", "is_active", "created_at")
    list_filter = ("is_active", "currency")
    search_fields = ("name", "description")
    inlines = [BenefitInline]
@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("product", "discount_percent", "discounted_price", "is_active", "valid_until")
    list_filter = ("is_active",)