from decimal import Decimal, InvalidOperation

from django.views.generic import ListView, DetailView
from django.shortcuts import render
from django.db.models import Q, Count
from .models import Product, Category


def home(request):
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0)
    latest_products = Product.objects.filter(is_active=True).select_related('category')[:8]
    return render(request, 'home.html', {
        'categories': categories,
        'latest_products': latest_products,
    })


def _parse_price(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


class CatalogView(ListView):
    model = Product
    template_name = 'products/catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        category_slug = self.request.GET.get('category')
        q = self.request.GET.get('q')
        min_price = _parse_price(self.request.GET.get('min_price'))
        max_price = _parse_price(self.request.GET.get('max_price'))

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['q'] = self.request.GET.get('q', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        # Строка запроса без параметра page — для ссылок пагинации
        params = self.request.GET.copy()
        params.pop('page', None)
        context['query_string'] = params.urlencode()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category, is_active=True
        ).exclude(id=self.object.id)[:4]
        return context


def search_products(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True).select_related('category')
    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
    else:
        products = products.none()
    return render(request, 'products/search_results.html', {'products': products, 'query': query})
