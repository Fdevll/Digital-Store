from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from products.models import generate_unique_slug


class Seller(models.Model):
    """Продавец-магазин на площадке: один аккаунт пользователя — один магазин."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller')
    shop_name = models.CharField('Название магазина', max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Продавец'
        verbose_name_plural = 'Продавцы'
        ordering = ['shop_name']

    def __str__(self):
        return self.shop_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self.shop_name, Seller, self.id)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('seller_shop', args=[self.slug])
