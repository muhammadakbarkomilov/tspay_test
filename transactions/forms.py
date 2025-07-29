from django import forms
from django.core.exceptions import ValidationError

from .models import Shop
from django.contrib.auth.forms import UserChangeForm
from accounts.models import CustomUser, Profile  # <-- Profile import qilingan

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['title', 'description', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(max_length=254, required=False)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'phone_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['phone_number'].initial = user.phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_qs = CustomUser.objects.filter(email=email).exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise ValidationError("Bu email boshqa foydalanuvchiga tegishli.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user

        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        user.phone_number = self.cleaned_data.get('phone_number')

        if commit:
            user.save()
            profile.save()

        return profile