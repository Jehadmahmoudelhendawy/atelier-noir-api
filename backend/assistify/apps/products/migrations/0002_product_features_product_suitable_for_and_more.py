from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ("products", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="product",
            name="features",
            field=models.JSONField(
                blank=True, default=list, help_text="List of product features"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="suitable_for",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="List of user types or conditions this is suitable for",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="use_cases",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="List of scenarios where this product is used",
            ),
        ),
    ]