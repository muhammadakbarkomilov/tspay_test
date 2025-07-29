import datetime

from django.db import models
from ckeditor.fields import RichTextField

class SitePolicy(models.Model):
    POLICY_CHOICES = (
        ('terms', 'Foydalanish shartlari'),
        ('privacy', 'Mahfiylik siyosati'),
    )
    title = models.CharField(max_length=100, choices=POLICY_CHOICES, unique=True)
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_title_display()