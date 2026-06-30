from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_product_image_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='gender',
            field=models.CharField(
                choices=[('men', 'Men'), ('women', 'Women'), ('unisex', 'Unisex')],
                default='unisex',
                max_length=10,
            ),
        ),
    ]
