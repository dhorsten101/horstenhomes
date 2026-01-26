from django.urls import path

from apps.branding import views

app_name = "branding"

urlpatterns = [
	path("", views.TenantBrandingUpdateView.as_view(), name="edit"),
	path("theme/", views.tenant_theme_update_view, name="theme_update"),
	path("theme/select/", views.user_theme_select_view, name="theme_select"),
]

