from django.contrib import admin
from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'message', 'user__username')
    list_editable = ('status',)
    readonly_fields = ('user', 'subject', 'message', 'created_at', 'updated_at')
    fields = ('user', 'subject', 'message', 'created_at', 'updated_at', 'status', 'answer')
