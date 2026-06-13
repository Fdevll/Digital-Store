from django import forms

from .models import SupportTicket


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'message']
        labels = {'subject': 'Тема', 'message': 'Сообщение'}
        widgets = {
            'message': forms.Textarea(attrs={'rows': 6}),
        }
