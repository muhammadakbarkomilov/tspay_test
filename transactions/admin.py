import requests
from django.contrib import admin

from notification.models import Notification
from .models import *
from accounts.models import *
from transactions.utils import send_telegram_message

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id','cheque_id','shop', 'amount', 'status', 'created_at')
    search_fields = ('cheque_id',)

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('shop_id', 'title', 'status')
    search_fields = ('shop_id',)

    def save_model(self, request, obj, form, change):
        old_status = None
        if obj.pk:
            old_status = Shop.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        # Faqat status o‘zgarganida ishlaydi
        if old_status != obj.status:
            if hasattr(obj.owner, 'telegram_id'):
                if obj.status == 'active':
                    # Telegramga yuborish
                    send_telegram_message(
                        obj.owner.telegram_id,
                        f"✅ Hurmatli @{obj.owner.telegram_username}, do‘koningiz '{obj.title}' tasdiqlandi!"
                    )
                    # Sayt notifikatsiyasi
                    Notification.objects.create(
                        user=obj.owner,
                        message=f"Do‘koningiz '{obj.title}' tasdiqlandi.",
                        notification_type="Do‘kon tasdiqlandi",
                        related_id=obj.id
                    )

                elif obj.status == 'canceled':
                    send_telegram_message(
                        obj.owner.telegram_id,
                        f"❌ Hurmatli @{obj.owner.telegram_username}, do‘koningiz '{obj.title}' tasdiqlanmadi, bu haqida qo'llab-quvvatlash markazi bilan bog'lanib bilib olishingiz mumkin!."
                    )
                    Notification.objects.create(
                        user=obj.owner,
                        message=f"Do‘koningiz '{obj.title}' tasdiqlanmadi, bu haqida qo'llab-quvvatlash markazi bilan bog'lanib bilib olishingiz mumkin!",
                        notification_type="Do‘kon rad etildi",
                        related_id=obj.id
                    )