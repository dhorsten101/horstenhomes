from __future__ import annotations

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedUUIDModel


class UnitInvoice(TimeStampedUUIDModel):
	"""Single-line invoice amount for a unit (tenant revenue)."""

	unit = models.ForeignKey("properties.Unit", on_delete=models.CASCADE, related_name="invoices")
	issue_date = models.DateField(default=timezone.now, db_index=True)
	amount = models.DecimalField(max_digits=14, decimal_places=2)
	description = models.CharField(max_length=500, blank=True)

	class Meta:
		ordering = ("-issue_date", "-created_at")
		indexes = [
			models.Index(fields=["unit", "issue_date"]),
		]

	def __str__(self) -> str:
		return f"Invoice {self.issue_date} — {self.unit}"


class UnitExpense(TimeStampedUUIDModel):
	"""Cost recorded against a unit."""

	unit = models.ForeignKey("properties.Unit", on_delete=models.CASCADE, related_name="expenses")
	expense_date = models.DateField(default=timezone.now, db_index=True)
	amount = models.DecimalField(max_digits=14, decimal_places=2)
	description = models.CharField(max_length=500, blank=True)

	documents = GenericRelation("documents.Document", related_query_name="unit_expense")

	class Meta:
		ordering = ("-expense_date", "-created_at")
		indexes = [
			models.Index(fields=["unit", "expense_date"]),
		]

	def delete(self, *args, **kwargs):
		self.documents.all().delete()
		super().delete(*args, **kwargs)

	def __str__(self) -> str:
		return f"Expense {self.expense_date} — {self.unit}"


class AssetCapitalInvestment(TimeStampedUUIDModel):
	"""Capital added to a property or unit (improvements, not operating expense)."""

	related_property = models.ForeignKey(
		"properties.Property",
		null=True,
		blank=True,
		on_delete=models.CASCADE,
		related_name="capital_investments",
	)
	unit = models.ForeignKey(
		"properties.Unit",
		null=True,
		blank=True,
		on_delete=models.CASCADE,
		related_name="capital_investments",
	)
	investment_date = models.DateField(default=timezone.now, db_index=True)
	amount = models.DecimalField(max_digits=14, decimal_places=2)
	description = models.CharField(max_length=500, blank=True)

	class Meta:
		ordering = ("-investment_date", "-created_at")
		indexes = [
			models.Index(fields=["related_property", "investment_date"]),
			models.Index(fields=["unit", "investment_date"]),
		]
		constraints = [
			models.CheckConstraint(
				condition=(
					models.Q(related_property__isnull=False, unit__isnull=True)
					| models.Q(related_property__isnull=True, unit__isnull=False)
				),
				name="accounting_capital_investment_property_xor_unit",
			),
		]

	def clean(self):
		from django.core.exceptions import ValidationError

		has_property = self.related_property_id is not None
		has_unit = self.unit_id is not None
		if has_property == has_unit:
			raise ValidationError("Link the investment to exactly one property or unit.")

	def save(self, *args, **kwargs):
		return super().save(*args, **kwargs)

	@property
	def asset_label(self) -> str:
		if self.unit_id:
			return f"{self.unit.property.name} · {self.unit.unit_number}"
		if self.related_property_id:
			return self.related_property.name
		return "Asset"

	def __str__(self) -> str:
		label = (self.description or "Capital investment").strip()
		return f"{label} — {self.asset_label}"
