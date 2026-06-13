from django.urls import path
from . import views

urlpatterns = [
    path('become/', views.become_seller, name='become_seller'),
    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('shop/edit/', views.edit_shop, name='seller_edit_shop'),
    path('sales/', views.seller_sales, name='seller_sales'),
    path('sales/report/', views.seller_report, name='seller_report'),
    path('products/new/', views.product_create, name='seller_product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='seller_product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='seller_product_delete'),
    path('<slug:slug>/', views.seller_shop, name='seller_shop'),
]
