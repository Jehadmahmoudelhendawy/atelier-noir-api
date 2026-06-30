from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0002_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="conversation",
            name="language",
            field=models.CharField(default="en", max_length=10),
        ),
        migrations.AddField(
            model_name="conversation",
            name="last_intent",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="conversation",
            name="last_product_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conversation",
            name="user_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]