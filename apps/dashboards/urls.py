from django.urls import path

from apps.dashboards import views

app_name = "dashboards"

urlpatterns = [
	path("units/<int:pk>/pnl/", views.UnitPnlDashboardView.as_view(), name="unit_pnl"),
	path("properties/<int:pk>/pnl/", views.PropertyPnlDashboardView.as_view(), name="property_pnl"),
	path("portfolios/<int:pk>/pnl/", views.PortfolioPnlDashboardView.as_view(), name="portfolio_pnl"),
]
