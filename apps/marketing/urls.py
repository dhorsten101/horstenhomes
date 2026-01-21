from django.urls import path
from . import views

app_name = "marketing"

urlpatterns = [
	path("", views.landing_view, name="landing"),
	path("pricing/", views.pricing_view, name="pricing"),
]