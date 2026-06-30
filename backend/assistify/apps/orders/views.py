from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order, Review
from .serializers import OrderSerializer, PlaceOrderSerializer, ReviewSerializer
class PlaceOrderView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        extra = {}
        if request.user.is_authenticated:
            extra["user"] = request.user
        order = serializer.save(**extra)
        return Response(
            {
                "message": "Order placed successfully.",
                "order": OrderSerializer(order).data,
            },
            status=status.HTTP_201_CREATED,
        )
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Order.objects.prefetch_related("items", "tracking_updates").all()
        return Order.objects.prefetch_related("items", "tracking_updates").filter(
            user=user
        )
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "order_number"
    def get_queryset(self):
        return Order.objects.prefetch_related("items", "tracking_updates")
class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)