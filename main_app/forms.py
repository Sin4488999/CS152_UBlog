from django.contrib.auth.forms import UserCreationForm
from django.db import models
from .models import Post, CustomUser, Profile
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
import re


class UserRegisterForm(UserCreationForm):
    # Use a form field for email input
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        """
        Username must be present and UNIQUE in a case-sensitive way.
        """
        username = self.cleaned_data.get("username", "")
        if not username:
            raise ValidationError("Please enter a username.")

        # Case-sensitive uniqueness check
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("That username is already taken.")

        return username

    def clean_email(self):
        """
        Email must be syntactically valid and unique (case-insensitive).
        """
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("Please enter an email address.")

        # Basic format validation
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")

        # Uniqueness (case-insensitive)
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")

        return email

    def clean_password2(self):
        """
        Combine:
          - Django's global AUTH_PASSWORD_VALIDATORS (via validate_password)
          - Your custom rules: must contain digit, uppercase, special char
          - Ensure password1 == password2
        """
        password1 = self.cleaned_data.get("password1") or ""
        password2 = self.cleaned_data.get("password2") or ""

        messages = []

        # Match check (what UserCreationForm normally enforces)
        if password1 and password2 and password1 != password2:
            messages.append("The two password fields didn’t match.")

        if password2:
            # Run global validators from AUTH_PASSWORD_VALIDATORS
            try:
                # user=None is fine here; validators that need user handle None
                validate_password(password2, user=None)
            except ValidationError as e:
                messages.extend(e.messages)

            # Extra strength rules on top of Django's validators
            if not re.search(r"\d", password2):
                messages.append("Password must contain at least one number.")
            if not re.search(r"[A-Z]", password2):
                messages.append("Password must contain at least one uppercase letter.")
            if not re.search(r"[^A-Za-z0-9]", password2):
                messages.append("Password must contain at least one special character.")

        # If anything failed, raise a combined ValidationError
        if messages:
            raise ValidationError(messages)

        return password2


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'content')

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(required=False)

    class Meta:
        model = Profile
        fields = ['bio']
