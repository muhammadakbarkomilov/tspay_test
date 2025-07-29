import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction

BOT_TOKEN = '8114840874:AAGr-myWUesy1GeoNcal2ltdyDjbNoKva9o'

def send_telegram_message(chat_id, message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f'Telegramga xabar yuborishda xatolik: {e}')

class Command(BaseCommand):
    help = '10 daqiqa o‘tgan pending to‘lovlarni canceled qilish'

    def handle(self, *args, **kwargs):
        deadline = timezone.now() - timedelta(minutes=10)
        expired = Transaction.objects.select_related('shop__owner').filter(status='pending', created_at__lt=deadline)

        count = 0
        for transaction in expired:
            transaction.status = 'canceled'
            transaction.save(update_fields=['status'])

            # Xabar yuborish
            tg_id = getattr(transaction.shop.owner, 'telegram_id', None)
            if tg_id:
                message = f"❗️ <b>{transaction.shop.title}</b> do‘konidagi\n🆔 <b>To‘lov ID:</b> <code>{transaction.cheque_id}</code>\n💰 <b>{transaction.amount:,}</b> UZS\n⏳ 10 daqiqa ichida to‘lanmadi, bekor qilindi."
                send_telegram_message(tg_id, message)

            count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} ta to‘lov bekor qilindi.'))