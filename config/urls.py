from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('users/', include('users.urls')),
    path('payments/', include('payments.urls')),
    path('sellers/', include('sellers.urls')),
    # Медиафайлы (превью товаров) отдаёт Django и в продакшене:
    # проект рассчитан на один сервер без отдельного файлового хранилища
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('', include('products.urls')),
]
