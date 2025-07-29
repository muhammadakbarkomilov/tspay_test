from django.contrib import admin
from .models import BlogPost, Tag
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget


class BlogPostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget(config_name='default'))
    summary = forms.CharField(widget=CKEditorUploadingWidget(config_name='default'))

    class Meta:
        model = BlogPost
        fields = '__all__'


class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm
    list_display = ('title', 'created_at', 'updated_at', 'views', 'clicks')
    list_filter = ('tags', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('views', 'clicks', 'post_id')

    class Media:
        css = {
            'all': ('ckeditor/ckeditor.css',)
        }


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Tag)