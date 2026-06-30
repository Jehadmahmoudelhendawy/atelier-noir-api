from django.db import migrations, models
class Migration(migrations.Migration):
    initial = True
    dependencies = [
    ]
    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(editable=False, max_length=50, unique=True)),
                ('customer_email', models.EmailField(max_length=254)),
                ('status', models.CharField(choices=[('placed', 'Order Placed'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('in_transit', 'In Transit'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='placed', max_length=20)),
                ('payment_method', models.CharField(choices=[('card', 'Credit/Debit Card'), ('cod', 'Cash on Delivery')], default='cod', max_length=10)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('shipping_fee', models.DecimalField(decimal_places=2, default=50, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('delivery_address', models.TextField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('tracking_number', models.CharField(blank=True, max_length=50)),
                ('estimated_delivery', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'orders',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=255)),
                ('product_emoji', models.CharField(blank=True, max_length=10)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveSmallIntegerField(default=1)),
            ],
            options={
                'db_table': 'order_items',
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'reviews',
            },
        ),
        migrations.CreateModel(
            name='TrackingUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('status', models.CharField(max_length=50)),
                ('location', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'tracking_updates',
                'ordering': ['date'],
            },
        ),
    ]