import io
import re

from django.core.management import call_command
from django.db.models import Q
from decouple import config
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, Offer
from .serializers import ProductSerializer, ProductWriteSerializer, OfferSerializer

# Colloquial / formal color words (Arabic + English) -> canonical Product.color,
# so a search like "بدلة سودا" still finds black suits.
SEARCH_COLOR_MAP = {
    "سودا": "Black", "سوده": "Black", "سودة": "Black", "أسود": "Black", "اسود": "Black", "black": "Black",
    "بيضا": "White", "بيضاء": "White", "أبيض": "White", "ابيض": "White", "white": "White",
    "حمرا": "Red", "حمراء": "Red", "أحمر": "Red", "احمر": "Red", "red": "Red",
    "كحلي": "Navy Blue", "كحلية": "Navy Blue", "navy": "Navy Blue",
    "نبيتي": "Burgundy", "خمري": "Burgundy", "برجاندي": "Burgundy", "برغندي": "Burgundy", "burgundy": "Burgundy",
    "فضي": "Silver", "فضى": "Silver", "رصاصي": "Grey", "رمادي": "Grey", "grey": "Grey", "gray": "Grey",
    "بني": "Brown", "brown": "Brown", "جملي": "Camel", "camel": "Camel", "بيج": "Beige", "beige": "Beige",
    "ذهبي": "Gold", "دهبي": "Gold", "gold": "Gold",
    "خضرا": "Emerald", "خضراء": "Emerald", "أخضر": "Emerald", "اخضر": "Emerald", "زمردي": "Emerald", "emerald": "Emerald",
    "وردي": "Pink", "بمبي": "Pink", "زهري": "Pink", "pink": "Pink",
    "لافندر": "Lavender", "lavender": "Lavender", "شامبني": "Champagne", "champagne": "Champagne",
}

# Colloquial item-type words -> substrings that appear in product names, so a
# search like "جزمة" finds the oxford shoes.
SEARCH_TYPE_MAP = {
    "جزمة": ["Oxford", "حذاء"], "جزم": ["Oxford", "حذاء"], "حذاء": ["Oxford", "حذاء"],
    "صندل": ["Heeled", "صندل"], "كعب": ["Heeled", "صندل"],
    "بدلة": ["Suit", "بدلة"], "بدله": ["Suit", "بدلة"], "بدل": ["Suit", "بدلة"],
    "فستان": ["Dress", "Gown", "فستان"], "فساتين": ["Dress", "Gown", "فستان"],
    "كرافتة": ["Tie", "كرافتة"], "كرفتة": ["Tie", "كرافتة"], "كرافتات": ["Tie", "كرافتة"],
    "جرافتة": ["Tie", "كرافتة"], "جرافته": ["Tie", "كرافتة"], "جرافت": ["Tie", "كرافتة"], "جرافتات": ["Tie", "كرافتة"], "قرافتة": ["Tie", "كرافتة"],
    "بليزر": ["Blazer", "بليزر"], "بالطو": ["Overcoat", "بالطو"], "معطف": ["Overcoat", "بالطو"],
    "قميص": ["Shirt", "قميص"], "قمصان": ["Shirt", "قميص"], "بلوزة": ["Blouse", "بلوزة"],
    "حزام": ["Belt", "حزام"], "بابيون": ["Bow Tie", "بابيون"], "وشاح": ["Scarf", "إيشارب"],
    "إيشارب": ["Scarf", "إيشارب"], "ايشارب": ["Scarf", "إيشارب"], "منديل": ["Pocket", "منديل"],
}


class IsAdminUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_admin_user
class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUserOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductWriteSerializer
        return ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).prefetch_related("benefits", "related_products")
        search = self.request.query_params.get("search", "").strip()
        if not search:
            return qs
        # Each word must match somewhere (name/description/color/category),
        # with colloquial color words mapped to the real color value.
        for token in [t for t in re.split(r"\s+", search.lower()) if len(t) >= 2]:
            sub = Q(name__icontains=token) | Q(description__icontains=token) | Q(color__icontains=token) | Q(category__icontains=token)
            mapped = SEARCH_COLOR_MAP.get(token)
            if mapped:
                sub |= Q(color=mapped)
            for syn in SEARCH_TYPE_MAP.get(token, []):
                sub |= Q(name__icontains=syn)
            qs = qs.filter(sub)
        return qs.distinct()
class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.prefetch_related("benefits", "related_products")
    permission_classes = [IsAdminUserOrReadOnly]
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProductWriteSerializer
        return ProductSerializer
    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        product.is_active = False
        product.save()
        return Response({"message": "Product deactivated."})
class OfferListView(generics.ListAPIView):
    queryset = Offer.objects.filter(is_active=True).select_related("product")
    serializer_class = OfferSerializer
    permission_classes = [permissions.AllowAny]


class SeedDatabaseView(APIView):
    """One-time, secret-protected endpoint to apply migrations and seed the
    formal-wear catalog on a serverless deployment where no shell is available.

    Protect it with the SEED_SECRET env var. If SEED_SECRET is unset/empty the
    endpoint is disabled (returns 403). Send the secret via the
    `X-Seed-Secret` header. Remove SEED_SECRET (or this route) once seeded.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        expected = config("SEED_SECRET", default="")
        provided = request.headers.get("X-Seed-Secret", "")
        if not expected or provided != expected:
            return Response(
                {"detail": "Forbidden. Set SEED_SECRET and send a matching X-Seed-Secret header."},
                status=status.HTTP_403_FORBIDDEN,
            )
        out = io.StringIO()
        try:
            call_command("migrate", interactive=False, stdout=out)
            call_command("seed_products", stdout=out)
        except Exception as exc:  # surface the error so it can be diagnosed
            return Response(
                {"success": False, "error": str(exc), "log": out.getvalue()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({
            "success": True,
            "product_count": Product.objects.count(),
            "offer_count": Offer.objects.count(),
            "log": out.getvalue(),
        })