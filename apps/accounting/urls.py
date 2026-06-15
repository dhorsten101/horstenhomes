from django.urls import path

from apps.accounting import views

app_name = "accounting"

urlpatterns = [
	path("units/<int:unit_pk>/invoices/new/", views.UnitInvoiceCreateView.as_view(), name="unit_invoice_create"),
	path("units/<int:unit_pk>/expenses/new/", views.UnitExpenseCreateView.as_view(), name="unit_expense_create"),
	path(
		"units/<int:unit_pk>/capital-investments/new/",
		views.UnitCapitalInvestmentCreateView.as_view(),
		name="unit_capital_investment_create",
	),
	path(
		"properties/<int:property_pk>/capital-investments/new/",
		views.PropertyCapitalInvestmentCreateView.as_view(),
		name="property_capital_investment_create",
	),
	path(
		"capital-investments/<int:pk>/edit/",
		views.CapitalInvestmentUpdateView.as_view(),
		name="capital_investment_update",
	),
	path(
		"capital-investments/<int:pk>/delete/",
		views.CapitalInvestmentDeleteView.as_view(),
		name="capital_investment_delete",
	),
]
