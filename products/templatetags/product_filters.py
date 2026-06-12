from django import template
from django.db.models import Count

from products.models import Category

register = template.Library()


@register.simple_tag
def get_categories_with_counts():
    return Category.objects.annotate(product_count=Count('products')).filter(product_count__gt=0)
