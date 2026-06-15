from django.contrib import admin

from apps.accounting.models import UnitExpense, UnitInvoice


@admin.register(UnitInvoice)
class UnitInvoiceAdmin(admin.ModelAdmin):
	list_display = ("issue_date", "amount", "unit", "created_at")
	list_filter = ("issue_date",)
	search_fields = ("description", "unit__unit_number", "unit__property__name")


@admin.register(UnitExpense)
class UnitExpenseAdmin(admin.ModelAdmin):
	list_display = ("expense_date", "amount", "unit", "created_at")
	list_filter = ("expense_date",)
	search_fields = ("description", "unit__unit_number", "unit__property__name")
