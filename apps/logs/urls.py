from django.urls import path

from . import views

app_name = "logs"

urlpatterns = [
	path("client/", views.client_log_view, name="client_log"),
]

