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
