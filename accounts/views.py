import smtplib

from django.conf import settings
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordResetDoneView, PasswordResetConfirmView,
                                       PasswordResetCompleteView)
from django.views.generic import FormView
from accounts.forms import RegisterForm, CustomPasswordResetForm, CustomSetPasswordForm, CustomAuthenticationForm
import socket
from smtplib import SMTPException

from django.contrib.auth.views import PasswordResetView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
import traceback


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)


class CustomRegisterView(FormView):
    template_name = 'accounts/registration.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()

        # ✅ SUCCESS MESSAGE
        messages.success(
            self.request,
            f"Account created successfully. Please log in."
        )

        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password-reset.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy("login")

    email_template_name = "accounts/email/password_reset_email.txt"
    html_email_template_name = "accounts/email/password_reset_email.html"
    subject_template_name = "accounts/email/password_reset_subject.txt"

    def form_valid(self, form):
        try:
            form.save(
                request=self.request,
                use_https=self.request.is_secure(),
                email_template_name = self.email_template_name,
                html_email_template_name = self.html_email_template_name,
                subject_template_name = self.subject_template_name)

            # ✅ Only shown if email sending REALLY succeeded
            messages.success(
                self.request,
                "If an account exists with this email, a password reset link has been sent."
            )
            return redirect(self.success_url)

        except (SMTPException, socket.timeout, TimeoutError,
                ConnectionRefusedError, OSError, smtplib.SMTPRecipientsRefused) as e:

            messages.error(
                self.request,
                "Unable to send password reset email right now. Please try again later or contact support."
            )
            return redirect(self.success_url)

        except Exception as e:
            print("PASSWORD RESET ERROR:", e)
            traceback.print_exc()

            messages.error(
                self.request,
                "Password reset failed due to a system error. Please try again later."
            )
            return redirect(self.success_url)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/login.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy("login")


    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Password reset successful. Please log in with your new password."
        )
        return response


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/login.html'
