from rest_framework import serializers
from .models import Order, OrderItem, TrackingUpdate, Review
class TrackingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingUpdate
        fields = ("date", "status", "location")
class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()
    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "product_emoji", "unit_price", "quantity", "line_total")
class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
class PlaceOrderSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    delivery_address = serializers.CharField(required=True, allow_blank=False)
    phone = serializers.CharField(required=True, allow_blank=False)
    items = OrderItemInputSerializer(many=True, min_length=1)
    def validate_items(self, items):
        from assistify.apps.products.models import Product
        validated = []
        for item in items:
            try:
                product = Product.objects.get(id=item["product_id"], is_active=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError(
                    f"Product {item['product_id']} not found or inactive."
                )
            validated.append({"product": product, "quantity": item["quantity"]})
        return validated
    def create(self, validated_data):
        from decimal import Decimal
        from django.utils import timezone
        import datetime
        items_data = validated_data.pop("items")
        subtotal = sum(
            item["product"].price * item["quantity"] for item in items_data
        )
        shipping = Decimal("50.00")
        total = subtotal + shipping
        user = validated_data.get("user")
        if user:
            update_fields = []
            if not user.address and validated_data.get("delivery_address"):
                user.address = validated_data["delivery_address"]
                update_fields.append("address")
            if not user.phone and validated_data.get("phone"):
                user.phone = validated_data["phone"]
                update_fields.append("phone")
            if update_fields:
                user.save(update_fields=update_fields)

        order = Order.objects.create(
            subtotal=subtotal,
            shipping_fee=shipping,
            total=total,
            estimated_delivery=(timezone.now().date() + datetime.timedelta(days=7)),
            **validated_data,
        )
        for item in items_data:
            product = item["product"]
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_emoji=product.emoji,
                unit_price=product.price,
                quantity=item["quantity"],
            )
        TrackingUpdate.objects.create(
            order=order,
            date=timezone.now().date(),
            status="Order Placed",
            location="Warehouse",
        )

        import threading
        def post_order_tasks(order_obj, current_user):
            from assistify.apps.orders.shippo_service import create_test_shipment
            try:
                shippo_data = create_test_shipment(order_obj)
                if shippo_data:
                    order_obj.tracking_number = shippo_data["tracking_number"]
                    order_obj.tracking_url = shippo_data["tracking_url"]
                    order_obj.save(update_fields=["tracking_number", "tracking_url"])
                    
                    TrackingUpdate.objects.create(
                        order=order_obj,
                        date=timezone.now().date(),
                        status=f"Label Created ({shippo_data['tracking_number']})",
                        location="Shippo Facility"
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Shippo Integration Error: {e}")
            
            if current_user:
                from assistify.apps.users.services import generate_recommendations_for_user
                try:
                    generate_recommendations_for_user(current_user)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to generate recommendations post-order: {e}")

        thread = threading.Thread(target=post_order_tasks, args=(order, user))
        thread.start()
                
        return order
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking_updates = TrackingUpdateSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "customer_email",
            "status",
            "payment_method",
            "subtotal",
            "shipping_fee",
            "total",
            "delivery_address",
            "phone",
            "tracking_number",
            "tracking_url",
            "estimated_delivery",
            "items",
            "tracking_updates",
            "created_at",
            "updated_at",
        )
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id", "order", "rating", "comment", "created_at")
        read_only_fields = ("id", "created_at")
    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value