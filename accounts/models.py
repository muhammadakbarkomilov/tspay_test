import os
import secrets
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from django.conf import settings

def uuidgenerator():
    return str(uuid.uuid4())

def user_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"  # instance bu Profile, instance.user.id bu CustomUser.id
    return os.path.join("profile_pictures", filename)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Foydalanuvchi uchun email kerak')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', str(uuid.uuid4()))  # Dummy username

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)  # Superuser uchun
        extra_fields.setdefault('username', str(uuid.uuid4()))  # Dummy username

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = models.CharField(
        _('Username'),
        max_length=150,
        unique=True,  # Django admin panelda kerak bo‘ladi
        blank=False,
        null=False,
    )
    email = models.EmailField(_('Email Address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    uu_id = models.UUIDField(default=uuidgenerator, editable=False)
    telegram_id = models.CharField(max_length=50, blank=True, null=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    last_password_change = models.DateTimeField(auto_now_add=True)
    telegram_link_token = models.UUIDField(default=uuidgenerator, editable=False)
    is_verified = models.BooleanField(default=False, verbose_name=_('Is Verified'))
    is_blocked = models.BooleanField(default=False, verbose_name=_('Is Blocked'))
    blocked_msg = models.TextField(
        default='Sizning akkauntingiz bloklangan. Iltimos, admin bilan bog‘laning.',
        verbose_name=_('Blocked Message')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # createsuperuser uchun username qaytariladi

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=user_image_upload_path, blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} profili"

def shop_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.shop_id}.{ext}"
    return os.path.join("shop_images", filename)

class Shop(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Tasdiqlash kutilmoqda'),
        ('active', 'Tasdiqlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shops')
    shop_id = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(_('Shop Title'), max_length=100)
    image = models.ImageField(_('Shop Image'), upload_to=shop_image_upload_path, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'  # Do‘kon statusi uchun default qiymat
    )
    access_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    balance = models.DecimalField(_('Shop Balance'), max_digits=10, decimal_places=2, default=0)
    description = models.TextField(_('Shop Description'), null=True, blank=True)
    created_at = models.DateTimeField(_('Shop Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Shop Updated'), auto_now=True)

    def __str__(self):
        return self.title

    def update_balance(self):
        success_sum = self.transaction_set.filter(status='success').aggregate(
            total=Sum('amount'))['total'] or 0
        self.balance = success_sum
        self.save()

    def save(self, *args, **kwargs):
        if not self.access_token:
            self.access_token = secrets.token_hex(32)
        super().save(*args, **kwargs)