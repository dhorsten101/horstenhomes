from django.urls import path
from .views import signup_view, signup_done_view

urlpatterns = [
	path("signup/", signup_view, name="tenant_signup"),
	path("signup/done/", signup_done_view, name="tenant_signup_done"),
]