from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_formalwear_color_sizes'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_url',
            field=models.URLField(blank=True, help_text='URL of the product image', max_length=500),
        ),
    ]
