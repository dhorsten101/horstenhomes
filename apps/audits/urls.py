from django.urls import path

from . import views

urlpatterns = [
	path("audit/", views.audit_list, name="audit_list"),
	path("audit/<int:pk>/", views.audit_detail, name="audit_detail"),
]