from django import forms

from products.models import Product
from .models import Seller


class SellerForm(forms.ModelForm):
    """Создание/редактирование магазина продавца."""
    class Meta:
        model = Seller
        fields = ['shop_name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class SellerProductForm(forms.ModelForm):
    """Форма товара для продавца: без выбора продавца и slug — они проставляются автоматически."""
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'category',
                  'preview_image', 'digital_file', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
