from django.urls import path
from .views import MessengerWebhookView

urlpatterns = [
    path('webhook/', MessengerWebhookView.as_view(), name='messenger-webhook'),
]
