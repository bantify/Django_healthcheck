from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, AuthenticationForm
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives

from accounts.models import User

ALLOWED_DOMAINS = ("@qvantel.com", "@banglalink.net")


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        error_messages={
            "required": "Email is required",
            "invalid": "Enter a valid email address",
        }
    )

    mobile = forms.CharField(
        max_length=15,
        error_messages={
            "required": "Mobile number is required",
        }
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput,
        error_messages={
            "required": "Password is required",
        }
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput,
        error_messages={
            "required": "Confirm password is required",
        }
    )

    class Meta:
        model = User
        fields = ("email", "mobile", "password1", "password2")

    def clean_mobile(self):
        mobile = self.cleaned_data.get("mobile")

        if not mobile.isdigit():
            raise forms.ValidationError("Mobile number must contain only digits")

        if len(mobile) < 10:
            raise forms.ValidationError("Mobile number must be at least 10 digits")

        return mobile

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email.lower().endswith(ALLOWED_DOMAINS):
            raise forms.ValidationError(
                "Email must be a Qvantel or Banglalink email address"
            )

        return email


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        error_messages={
            "required": "Email is required",
            "invalid": "Enter a valid email address",
        },
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email.lower().endswith(ALLOWED_DOMAINS):
            raise forms.ValidationError(
                "Email must be a Qvantel or Banglalink email address"
            )
        return email


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        error_messages={"required": "New Password is required"},
        label="New Password",
    )

    new_password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        error_messages={"required": "Confirm Password is required"},
        label="Confirm New Password",
    )

    error_messages = {
        "password_mismatch": "The two password fields didn’t match.",
    }


# forms.py

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        required=True,
        error_messages={
            "required": "Email is required",
            "invalid": "Enter a valid email address",
        },
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=True,
        error_messages={
            "required": "Password is required",
        },
    )

    error_messages = {
        "invalid_login": "Invalid email or password. Please try again.",
        "inactive": "This account is inactive.",
    }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not username.lower().endswith(ALLOWED_DOMAINS):
            raise forms.ValidationError(
                "Email must be a Qvantel or Banglalink email address"
            )
        return username
