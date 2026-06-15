from django.urls import path

from apps.estate_agents import views

app_name = "estate_agents"

urlpatterns = [
	path("", views.EstateAgentListView.as_view(), name="list"),
	path("new/", views.EstateAgentCreateView.as_view(), name="create"),
	path("<int:pk>/", views.EstateAgentDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.EstateAgentUpdateView.as_view(), name="update"),
	path("<int:pk>/delete/", views.EstateAgentDeleteView.as_view(), name="delete"),
]
