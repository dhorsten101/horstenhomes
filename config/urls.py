from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

from apps.accounts.views import DevPasswordResetDoneView, DevPasswordResetView, tenant_aware_login_view

urlpatterns = [
    # Public marketing site (public schema)
    path("", include("apps.marketing.urls")),
    
    # Public onboarding (public schema)
    path("", include("apps.onboarding.urls")),
    
    # Tenant UI (tenant schema)
    path("", include("apps.web.urls")),

    # Tenant CRM (tenant schema only, enforced in views via tenant checks)
    path("crm/addresses/", include(("apps.addresses.urls", "addresses"), namespace="addresses")),
    path("crm/contacts/", include(("apps.contacts.urls", "contacts"), namespace="contacts")),
    path("crm/portfolios/", include(("apps.portfolio.urls", "portfolio"), namespace="portfolio")),
    path("crm/properties/", include(("apps.properties.urls", "properties"), namespace="properties")),
    path("crm/leases/", include(("apps.leases.urls", "leases"), namespace="leases")),
    path("crm/documents/", include(("apps.documents.urls", "documents"), namespace="documents")),
    path("crm/todo/", include(("apps.todo.urls", "todo"), namespace="todo")),
    path("crm/branding/", include(("apps.branding.urls", "branding"), namespace="branding")),
    
    path("", include("apps.audits.urls")),
    
    # Account pages (tenant-local)
    path("accounts/", include("apps.accounts.urls")),

    # Client/runtime logging endpoints (tenant-local and public)
    path("logs/", include("apps.logs.urls")),

    # Auth
    # - public schema: tenant locator (redirects to tenant host)
    # - tenant schema: normal login form
    path("login/", tenant_aware_login_view, name="login"),
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

    # Platform admin (public schema only; staff only)
    path("platform/", include("apps.platform.urls")),
    
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)