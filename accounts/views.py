import random
import time
import re

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from transactions.models import Transaction
from transactions.utils import send_sms_code, send_sms
from .forms import RegisterForm, LoginForm
from .models import Profile
from .permissions import IsNotBlocked
from .serializers import RegisterSerializer, UserSerializer, MyTokenObtainPairSerializer
from django.contrib.auth import get_user_model, login, logout

import requests

TELEGRAM_BOT_TOKEN = '8114840874:AAGr-myWUesy1GeoNcal2ltdyDjbNoKva9o'  # o'zingizning tokeningiz
TELEGRAM_CHAT_ID = '5815237885'  # o'zingizning Telegram ID yoki guruh ID

def send_telegram_message(message, endpoint='sendMessage', parse_mode='HTML', extra_data=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{endpoint}"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': parse_mode,
    }

    def send_sms(phone, message):
        API_URL = "https://sms.xusanboy-dev.uz/send-sms"  # O'zingizning API URL
        payload = {
            "phone": phone,
            "message": message,
        }

        try:
            response = requests.post(API_URL, data=payload)
            result = response.json()
            return result.get("success", False)
        except Exception as e:
            print("SMS yuborishda xatolik:", e)
            return False

    # Agar tashqi qo‘shimcha data bo‘lsa, birlashtiramiz
    if extra_data:
        data.update(extra_data)

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()  # xatolik bo‘lsa, Exception otadi
    except requests.RequestException as e:
        print("Telegramga yuborishda xatolik:", e)

CustomUser = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny, IsNotBlocked)
    serializer_class = RegisterSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permissions_classes = (permissions.AllowAny, IsNotBlocked)

class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsNotBlocked)
    serializer_class = UserSerializer

class UserDetailView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.IsAuthenticated,IsNotBlocked)
    serializer_class = UserSerializer
    lookup_field = 'id'


def clean_phone_number(phone):
    phone = re.sub(r'[^0-9]', '', str(phone))  # faqat raqamlarni qoldiradi
    if phone.startswith('998'):
        phone = phone  # allaqachon 998 bilan boshlangan
    elif phone.startswith('9') and len(phone) == 9:
        phone = '998' + phone
    return phone


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                phone = clean_phone_number(form.cleaned_data['phone_number'])
                code = str(random.randint(100000, 999999))

                # SMS yuborish oralig'ini tekshirish
                last_sent = cache.get(f"last_sms_sent_{phone}")
                if last_sent and (time.time() - last_sent) < 60:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Iltimos, 1 daqiqadan keyin qayta urunib ko\'ring'
                    }, status=400)

                # Session ma'lumotlarini saqlash
                request.session['temp_user_data'] = {
                    'email': form.cleaned_data['email'],
                    'username': form.cleaned_data['username'],
                    'password1': form.cleaned_data['password1'],
                    'phone_number': phone,
                    'first_name': form.cleaned_data.get('first_name', ''),
                    'last_name': form.cleaned_data.get('last_name', '')
                }
                request.session.modified = True

                # SMS yuborish (simulyatsiya)
                print(f"SMS kod yuborildi: {phone} - {code}")  # Debug uchun
                send_sms_code(phone, code)
                cache.set(f"sms_code_{phone}", code, timeout=300)
                cache.set(f"last_sms_sent_{phone}", time.time(), timeout=60)

                return JsonResponse({'status': 'ok', 'message': 'SMS yuborildi'})

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Xatolik yuz berdi: ' + str(e)
                }, status=500)
        else:
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)

    # GET so'rovi uchun HTML sahifasini qaytarish
    form = RegisterForm()
    return render(request, 'my/register.html', {'form': form})


@csrf_exempt
def verify_sms_code(request):
    if request.method == 'POST':
        try:
            code = request.POST.get('code', '').strip()
            if not code or len(code) != 6 or not code.isdigit():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Noto\'g\'ri kod formati'
                }, status=400)

            session_data = request.session.get('temp_user_data')
            if not session_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Sessiya tugagan. Iltimos, qayta ro\'yxatdan o\'ting.'
                }, status=400)

            phone = session_data.get('phone_number')
            if not phone:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Telefon raqami topilmadi'
                }, status=400)

            correct_code = cache.get(f"sms_code_{phone}")
            if not correct_code:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Kodning muddati tugagan yoki noto\'g\'ri'
                }, status=400)

            if code != correct_code:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Noto\'g\'ri kod'
                }, status=400)

            # Foydalanuvchi yaratish
            user = CustomUser.objects.create_user(
                email=session_data['email'],
                username=session_data['username'],
                password=session_data['password1'],
                phone_number=phone,
                first_name=session_data.get('first_name', ''),
                last_name=session_data.get('last_name', '')
            )

            login(request, user)

            # Tozalash
            request.session.pop('temp_user_data', None)
            cache.delete(f"sms_code_{phone}")

            return JsonResponse({'status': 'ok', 'redirect_url': '/dashboard/'})

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Xatolik yuz berdi: ' + str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Noto\'g\'ri so\'rov'
    }, status=400)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip_address:
                ip_address = ip_address.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', 'Nomaʼlum qurilma')
            sms_text = f"Diqqat tizimga kirish aniqlandi.\nIP: {ip_address}\nQurilma: {user_agent}"
            send_sms(user.phone_number, sms_text)
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'my/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required()
def dashboard(request):
    # Stats Cards
    total_transactions = Transaction.objects.filter(shop__owner=request.user).count()

    shops_count = request.user.shops.count()

    today = timezone.now().date()
    today_income = Transaction.objects.filter(
        shop__owner=request.user,
        status='success',
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    success_transactions = Transaction.objects.filter(
        shop__owner=request.user,
        status='success'
    ).count()

    # Recent Transactions
    recent_transactions = (
        Transaction.objects
        .filter(shop__owner=request.user)
        .select_related('shop')
        .order_by('-created_at')[:5]
    )

    context = {
        'total_transactions': total_transactions,
        'today_income': today_income,
        'success_transactions': success_transactions,
        'recent_transactions': recent_transactions,
    }

    return render(request, 'my/dashboard.html', context)