from django.contrib import admin

from apps.accounting.models import AssetCapitalInvestment, UnitExpense, UnitInvoice


@admin.register(AssetCapitalInvestment)
class AssetCapitalInvestmentAdmin(admin.ModelAdmin):
	list_display = ("investment_date", "amount", "related_property", "unit", "created_at")
	list_filter = ("investment_date",)
	search_fields = ("description", "related_property__name", "unit__unit_number", "unit__property__name")


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
