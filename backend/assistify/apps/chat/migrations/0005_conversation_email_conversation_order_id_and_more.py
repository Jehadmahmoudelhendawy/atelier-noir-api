from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0004_conversation_address_conversation_purchase_state'),
    ]
    operations = [
        migrations.AddField(
            model_name='conversation',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='order_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='quantity',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]