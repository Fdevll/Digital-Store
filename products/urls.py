from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.CatalogView.as_view(), name='catalog'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('search/', views.search_products, name='search'),
]
