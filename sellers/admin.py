from django.contrib import admin
from .models import Seller


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('shop_name', 'user__username')
    prepopulated_fields = {'slug': ('shop_name',)}
    list_editable = ('is_active',)
