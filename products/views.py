from django.views.generic import ListView, DetailView
from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Product, Category


def home(request):
    categories = Category.objects.all()
    return render(request, 'home.html', {'categories': categories})

class CatalogView(ListView):
    model = Product
    template_name = 'products/catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_slug = self.request.GET.get('category')
        q = self.request.GET.get('q')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['q'] = self.request.GET.get('q', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category, is_active=True
        ).exclude(id=self.object.id)[:4]
        return context

def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(request, 'products/search_results.html', {'products': products, 'query': query})
