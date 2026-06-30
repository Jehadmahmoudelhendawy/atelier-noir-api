from django.urls import path
from .views import PlaceOrderView, OrderListView, OrderDetailView, ReviewCreateView
urlpatterns = [
    path("", PlaceOrderView.as_view(), name="order-place"),
    path("list/", OrderListView.as_view(), name="order-list"),
    path("<str:order_number>/", OrderDetailView.as_view(), name="order-detail"),
    path("reviews/create/", ReviewCreateView.as_view(), name="review-create"),
]