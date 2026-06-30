from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('assistify.apps.users.urls')),
    path('api/v1/products/', include('assistify.apps.products.urls')),
    path('api/v1/orders/', include('assistify.apps.orders.urls')),
    path('api/v1/chat/', include('assistify.apps.chat.urls')),
    path('api/v1/messenger/', include('assistify.apps.messenger.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
