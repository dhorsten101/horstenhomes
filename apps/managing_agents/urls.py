from django.urls import path

from apps.managing_agents import views

app_name = "managing_agents"

urlpatterns = [
	path("", views.ManagingAgentListView.as_view(), name="list"),
	path("new/", views.ManagingAgentCreateView.as_view(), name="create"),
	path("<int:pk>/", views.ManagingAgentDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.ManagingAgentUpdateView.as_view(), name="update"),
	path("<int:pk>/delete/", views.ManagingAgentDeleteView.as_view(), name="delete"),
]
