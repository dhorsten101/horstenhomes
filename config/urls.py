from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from apps.accounts.views import DevPasswordResetView, DevPasswordResetDoneView

urlpatterns = [
    # Public marketing site (public schema)
    path("", include("apps.marketing.urls")),
    
    # Public onboarding (public schema)
    path("", include("apps.onboarding.urls")),
    
    # Tenant UI (tenant schema)
    path("", include("apps.web.urls")),
    
    path("", include("apps.audits.urls")),
    
    # Account pages (tenant-local)
    path("accounts/", include("apps.accounts.urls")),

    # Auth (tenant-local; will also work on public schema if needed)
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password-reset/",
        DevPasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        DevPasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    # First-login "set password" flow (we generate a reset link during provisioning)
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    
    # Admin (public schema on admin.*; tenant schema on tenant hostnames)
    path("admin/", admin.site.urls),
    
]