from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import SupportTicketForm


def support(request):
    """Страница поддержки: пользователь оставляет обращение, оно сохраняется в БД."""
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
            ticket.save()
            messages.success(request, 'Обращение отправлено. Мы ответим вам в ближайшее время.')
            return redirect('support')
    else:
        form = SupportTicketForm()

    tickets = None
    if request.user.is_authenticated:
        tickets = request.user.support_tickets.all()
    return render(request, 'support/support.html', {'form': form, 'tickets': tickets})
