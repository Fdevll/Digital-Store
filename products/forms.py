from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'slug', 'description', 'price', 'category', 'preview_image', 'digital_file', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SearchForm(forms.Form):
    q = forms.CharField(max_length=100, required=False, label='Поиск')
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, label='Категория')
    min_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Цена от')
    max_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Цена до')
