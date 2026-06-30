from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0003_conversation_language_conversation_last_intent_and_more"),
    ]
    operations = [
        migrations.AddField(
            model_name="conversation",
            name="purchase_state",
            field=models.CharField(blank=True, help_text="Current step in purchase flow (e.g., 'awaiting_address')", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="conversation",
            name="address",
            field=models.TextField(blank=True, null=True),
        ),
    ]