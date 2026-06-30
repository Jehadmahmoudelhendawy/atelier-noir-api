from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0005_conversation_email_conversation_order_id_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='conversation',
            name='last_product_data',
            field=models.JSONField(blank=True, null=True),
        ),
    ]