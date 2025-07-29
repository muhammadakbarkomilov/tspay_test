from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email','username','phone_number', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')  # Chunki biz email orqali login qilamiz

    def confirm_login_allowed(self, user):
        pass

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'email']  # kerakli maydonlar

    bio = forms.CharField(widget=forms.Textarea, required=False)
    profile_picture = forms.ImageField(required=False)

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Profil (one-to-one) uchun ham saqlash
        profile = user.profile
        profile.bio = self.cleaned_data.get('bio')
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            profile.profile_picture = profile_picture
        if commit:
            profile.save()

        return user