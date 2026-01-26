from django.urls import path

from .views import signup_done_view, signup_status_view, signup_view

urlpatterns = [
	path("signup/", signup_view, name="tenant_signup"),
	path("signup/done/", signup_done_view, name="tenant_signup_done"),
	path("signup/status/<uuid:uid>/", signup_status_view, name="tenant_signup_status"),
]