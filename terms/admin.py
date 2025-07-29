from django.contrib import admin
from .models import SitePolicy

@admin.register(SitePolicy)
class SitePolicyAdmin(admin.ModelAdmin):
    list_display = ['title']