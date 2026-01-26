from django.urls import path

from apps.documents import views

app_name = "documents"

urlpatterns = [
	path("", views.DocumentListView.as_view(), name="list"),
	path("upload/", views.document_upload_view, name="upload"),
	path("<int:pk>/", views.DocumentDetailView.as_view(), name="detail"),
	path("<int:pk>/download/", views.document_download_view, name="download"),
	path("<int:pk>/edit/", views.DocumentUpdateView.as_view(), name="edit"),
	path("<int:pk>/delete/", views.DocumentDeleteView.as_view(), name="delete"),
]
