from decimal import Decimal
from django.apps import apps
from assistify.apps.orders.models import Order, OrderItem
def create_order_from_chat(product_id, phone, address, quantity=1, email="customer@example.com"):
    Product = apps.get_model("products", "Product")
    product = Product.objects.get(id=product_id)
    quantity = int(quantity or 1)
    subtotal = Decimal(str(product.price)) * quantity
    shipping_fee = Decimal("50.00")
    total = subtotal + shipping_fee
    order = Order.objects.create(
        customer_email=email,
        phone=phone,
        delivery_address=address,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total=total,
        payment_method=Order.PaymentMethod.COD,
        status=Order.Status.PLACED,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_emoji=getattr(product, "emoji", ""),
        unit_price=product.price,
        quantity=quantity,
    )
    return order