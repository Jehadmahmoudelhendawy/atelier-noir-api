from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_product_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(
                choices=[
                    ('suits', 'Suits & Tuxedos'),
                    ('dresses', 'Evening Dresses & Gowns'),
                    ('shirts', 'Shirts & Blouses'),
                    ('footwear', 'Formal Footwear'),
                    ('accessories', 'Accessories'),
                    ('outerwear', 'Coats & Blazers'),
                ],
                default='accessories',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='color',
            field=models.CharField(blank=True, help_text="Primary color of the item, e.g. 'Navy Blue'", max_length=50),
        ),
        migrations.AddField(
            model_name='product',
            name='sizes',
            field=models.JSONField(blank=True, default=list, help_text="List of available sizes, e.g. ['M','L','XL'] or ['42','43']"),
        ),
    ]
