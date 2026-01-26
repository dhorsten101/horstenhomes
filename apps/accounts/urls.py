from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
	# Compatibility with Django defaults / older links
	path("login/", views.tenant_aware_login_view, name="login"),
	path("logout/", auth_views.LogoutView.as_view(), name="logout"),
	path("profile/", views.profile_view, name="profile"),
	path("users/", views.TenantUserListView.as_view(), name="user_list"),
	path("users/create/", views.tenant_user_create_view, name="user_create"),
	path("users/<int:pk>/edit/", views.TenantUserUpdateView.as_view(), name="user_edit"),
	path("users/<int:pk>/set-password-link/", views.tenant_user_set_password_link_view, name="user_set_password_link"),
	path("users/<int:pk>/toggle-active/", views.tenant_user_toggle_active_view, name="user_toggle_active"),
]

