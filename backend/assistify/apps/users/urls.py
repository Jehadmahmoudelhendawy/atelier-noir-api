from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, MeView, NotificationListView, NotificationMarkReadView, TriggerRecommendationsView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("me/trigger-recommendations/", TriggerRecommendationsView.as_view(), name="trigger-recommendations"),
    path("notifications/", NotificationListView.as_view(), name="notifications-list"),
    path("notifications/mark-read/", NotificationMarkReadView.as_view(), name="notifications-mark-read-all"),
    path("notifications/<int:pk>/mark-read/", NotificationMarkReadView.as_view(), name="notifications-mark-read"),
]