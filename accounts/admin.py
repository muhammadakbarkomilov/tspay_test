from django.contrib import admin
from .models import CustomUser, Profile

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
   list_display = ['first_name', 'username', 'uu_id', 'email', 'phone_number', 'is_staff', 'is_active']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Profile._meta.fields]
    list_filter = ('user',)