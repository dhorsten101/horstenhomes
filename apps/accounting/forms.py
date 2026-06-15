from __future__ import annotations

from django import forms

from apps.accounting.models import AssetCapitalInvestment, UnitExpense, UnitInvoice
from apps.core.forms import BootstrapModelForm


class UnitInvoiceForm(BootstrapModelForm):
	class Meta:
		model = UnitInvoice
		fields = ("issue_date", "amount", "description")


class UnitExpenseForm(BootstrapModelForm):
	attachment = forms.FileField(
		required=False,
		label="Receipt or invoice (optional)",
		help_text="PDF, image, or other file stored with this expense.",
	)

	class Meta:
		model = UnitExpense
		fields = ("expense_date", "amount", "description")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.order_fields(("expense_date", "amount", "description", "attachment"))


class AssetCapitalInvestmentForm(BootstrapModelForm):
	class Meta:
		model = AssetCapitalInvestment
		fields = ("investment_date", "amount", "description")
