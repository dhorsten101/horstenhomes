from django.urls import path

from apps.rental_agents import views

app_name = "rental_agents"

urlpatterns = [
	path("", views.RentalAgentListView.as_view(), name="list"),
	path("new/", views.RentalAgentCreateView.as_view(), name="create"),
	path("<int:pk>/", views.RentalAgentDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.RentalAgentUpdateView.as_view(), name="update"),
	path("<int:pk>/delete/", views.RentalAgentDeleteView.as_view(), name="delete"),
]
