from django import template
from django.db.models import Count

register = template.Library()

@register.filter
def truncatewords_html(value, arg):
    try:
        length = int(arg)
    except ValueError:
        return value
    words = value.split()
    if len(words) > length:
        return ' '.join(words[:length]) + '...'
    return value

@register.simple_tag
def get_category_count():
    return Category.objects.annotate(product_count=Count('products')).filter(product_count__gt=0)
