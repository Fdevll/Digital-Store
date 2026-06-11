from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:order_id>/', views.payment_create, name='payment_create'),
    path('success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('fail/<int:order_id>/', views.payment_fail, name='payment_fail'),
    path('webhook/', views.payment_webhook, name='payment_webhook'),
]
