from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.datetime_safe import datetime

from .models import Notification
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    data = {
        'notifications': [
            {
                'message': n.message,
                'notification_id': n.id,
                'created_at': n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'is_read': n.is_read,
                'notification_type': n.notification_type
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

def broadcast_notification(message, notification_id, notification_type, created_at=None):
    channel_layer = get_channel_layer()
    if created_at is None:
        created_at = datetime.now()

    async_to_sync(channel_layer.group_send)(
        'notifications_broadcast',
        {
            'type': 'send_notification',  # bu 'send_notification' methodini chaqiradi
            'message': message,
            'notification_id': notification_id,
            'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': False,
            'notification_type': notification_type,
        }
    )