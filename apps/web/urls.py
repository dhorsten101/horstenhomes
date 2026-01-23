from django.urls import path
from . import views

urlpatterns = [
	path("", views.home_view, name="home"),
	path("crm/", views.crm_dashboard_view, name="crm_dashboard"),
]