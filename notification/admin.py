from django.contrib import admin
from notification.models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at', 'notification_type')
    list_filter = ('is_read', 'notification_type')
    search_fields = ('message', 'user__username')
    ordering = ('-created_at',)