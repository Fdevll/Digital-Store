from django.contrib import admin
from .models import Order, OrderItem, Download

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class DownloadInline(admin.TabularInline):
    model = Download
    extra = 0
    readonly_fields = ('download_token', 'created_at', 'expires_at')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'payment_id')
    inlines = [OrderItemInline, DownloadInline]
    date_hierarchy = 'created_at'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity')
    list_filter = ('order__status',)
    search_fields = ('product__title',)

@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'order', 'created_at', 'is_used', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'product__title')
    date_hierarchy = 'created_at'
