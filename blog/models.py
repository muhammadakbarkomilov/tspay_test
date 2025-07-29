from django.db import models
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
import uuid

def upload_post_photo(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"blog_photos/{filename}"

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = RichTextUploadingField()  # Rich text editor uchun
    summary = RichTextField(config_name='default')  # Qisqa tavsif uchun
    tags = models.ManyToManyField('Tag', blank=True)
    slug = models.SlugField(max_length=200)
    photo = models.ImageField(upload_to=upload_post_photo, blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    post_id = models.UUIDField(default=uuid.uuid4, editable=False)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

from django.utils.text import slugify

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if not self.slug or Tag.objects.filter(slug=base_slug).exclude(id=self.id).exists():
            unique_slug = base_slug
            num = 1
            while Tag.objects.filter(slug=unique_slug).exclude(id=self.id).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)