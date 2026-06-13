from django.db import models
from django.contrib.auth.models import User


class SupportTicket(models.Model):
    """Обращение пользователя в поддержку. Ответ даётся через админку."""
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('in_progress', 'В работе'),
        ('closed', 'Закрыто'),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='support_tickets',
        null=True, blank=True,
    )
    subject = models.CharField('Тема', max_length=200)
    message = models.TextField('Сообщение')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    answer = models.TextField('Ответ', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Обращение'
        verbose_name_plural = 'Обращения в поддержку'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} ({self.get_status_display()})'
