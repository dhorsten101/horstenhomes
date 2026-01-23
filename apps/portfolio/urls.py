from django.urls import path

from apps.portfolio import views

app_name = "portfolio"

urlpatterns = [
	path("", views.PortfolioListView.as_view(), name="list"),
	path("new/", views.PortfolioCreateView.as_view(), name="create"),
	path("<int:pk>/", views.PortfolioDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.PortfolioUpdateView.as_view(), name="update"),
	path("<int:pk>/delete/", views.PortfolioDeleteView.as_view(), name="delete"),
]

