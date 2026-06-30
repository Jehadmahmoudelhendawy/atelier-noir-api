from django.db import models
from django.conf import settings
class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    session_key = models.CharField(max_length=64, blank=True)
    last_product_id = models.IntegerField(null=True, blank=True)
    last_product_data = models.JSONField(null=True, blank=True)
    last_intent = models.CharField(max_length=50, null=True, blank=True)
    language = models.CharField(max_length=10, default="en")
    user_name = models.CharField(max_length=100, null=True, blank=True)
    purchase_state = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Current step in purchase flow (e.g., 'awaiting_address')",
    )
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    quantity = models.PositiveSmallIntegerField(null=True, blank=True)
    order_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at"]
    def __str__(self):
        identifier = self.user.email if self.user else self.session_key
        return f"Conversation {self.id} — {identifier}"
class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"