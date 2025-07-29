from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


def send_notification(user_id, message, notification_type, related_id=None):
    user = User.objects.get(id=user_id)
    notification = Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type,
        related_id=related_id
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type': 'send_notification',
            'message': message,
            'notification_id': notification.id,
            'created_at': notification.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'is_read': False,
            'notification_type': notification_type
        }
    )

    return notification