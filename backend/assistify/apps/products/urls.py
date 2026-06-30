from django.urls import path
from .views import (
    ProductListCreateView,
    ProductRetrieveUpdateDestroyView,
    OfferListView,
    SeedDatabaseView,
)
urlpatterns = [
    path("", ProductListCreateView.as_view(), name="product-list"),
    path("offers/", OfferListView.as_view(), name="offer-list"),
    path("admin/seed/", SeedDatabaseView.as_view(), name="product-seed"),
    path("<int:pk>/", ProductRetrieveUpdateDestroyView.as_view(), name="product-detail"),
]