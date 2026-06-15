from django.urls import path

from apps.accounting import views

app_name = "accounting"

urlpatterns = [
	path("units/<int:unit_pk>/invoices/new/", views.UnitInvoiceCreateView.as_view(), name="unit_invoice_create"),
	path("units/<int:unit_pk>/expenses/new/", views.UnitExpenseCreateView.as_view(), name="unit_expense_create"),
]
