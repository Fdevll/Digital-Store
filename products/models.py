from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import uuid


def transliterate_cyrillic(text):
    """Transliterate Cyrillic text to Latin for slug generation."""
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    }
    result = ''
    for char in text:
        result += cyrillic_to_latin.get(char, char)
    return result


def generate_unique_slug(title, model_class, instance_id=None):
    """Generate a unique slug from title."""
    # Try transliteration first, then slugify
    transliterated = transliterate_cyrillic(title)
    slug = slugify(transliterated)

    # Fall back to UUID if slug is empty
    if not slug:
        slug = f'product-{uuid.uuid4().hex[:8]}'

    # Ensure uniqueness
    original_slug = slug
    counter = 1
    queryset = model_class.objects.filter(slug=slug)
    if instance_id:
        queryset = queryset.exclude(id=instance_id)

    while queryset.exists():
        slug = f'{original_slug}-{counter}'
        counter += 1
        queryset = model_class.objects.filter(slug=slug)
        if instance_id:
            queryset = queryset.exclude(id=instance_id)

    return slug


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    seller = models.ForeignKey(
        'sellers.Seller', on_delete=models.SET_NULL,
        related_name='products', null=True, blank=True,
    )
    preview_image = models.ImageField(upload_to='products/previews/', blank=True, null=True)
    digital_file = models.FileField(upload_to='products/files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self.title, Product, self.id)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])
