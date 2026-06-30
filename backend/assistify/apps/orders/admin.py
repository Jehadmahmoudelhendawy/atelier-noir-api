from django.contrib import admin
from .models import Order, OrderItem, TrackingUpdate, Review
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)
class TrackingInline(admin.TabularInline):
    model = TrackingUpdate
    extra = 0
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_email", "status", "total", "payment_method", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("order_number", "customer_email")
    inlines = [OrderItemInline, TrackingInline]
    readonly_fields = ("order_number", "created_at", "updated_at")
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("order", "rating", "created_at")
    list_filter = ("rating",)