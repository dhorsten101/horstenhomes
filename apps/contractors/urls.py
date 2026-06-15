from django.urls import path

from apps.contractors import views

app_name = "contractors"

urlpatterns = [
	path("", views.ContractorListView.as_view(), name="list"),
	path("new/", views.ContractorCreateView.as_view(), name="create"),
	path("<int:pk>/", views.ContractorDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.ContractorUpdateView.as_view(), name="update"),
	path("<int:pk>/delete/", views.ContractorDeleteView.as_view(), name="delete"),
]
