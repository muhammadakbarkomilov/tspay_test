import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass  # Foydalanuvchidan kelgan xabarlarni qabul qilmaymiz

    async def send_notification(self, event):
        notification = await self.get_notification(event["notification_id"])
        if notification:
            await self.send(text_data=json.dumps({
                "type": "notification",
                "message": notification.message,
                "timestamp": notification.created_at.strftime("%Y-%m-%d %H:%M"),
                "notification_id": notification.id,
                "is_read": notification.is_read,
                "notification_type": notification.notification_type
            }))

    @database_sync_to_async
    def get_notification(self, notification_id):
        try:
            return Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return None