from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from apps.core.models import TimeStampedUUIDModel


class Portfolio(TimeStampedUUIDModel):
	name = models.CharField(max_length=200, db_index=True)
	description = models.TextField(blank=True)

	owner_contact = models.ForeignKey(
		"contacts.Contact",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="portfolios",
	)

	is_archived = models.BooleanField(default=False, db_index=True)

	class Meta:
		indexes = [
			models.Index(fields=["is_archived", "created_at"]),
		]

	def __str__(self) -> str:
		return self.name

	def total_asset_value(self) -> Decimal:
		"""
		Total purchase value of all assets in this portfolio:
		- site/base value: sum(Property.purchase_price)
		- unit value: sum(Unit.purchase_price) across all properties
		(total = site + unit)

		If the queryset annotated `total_asset_value`, that value is used.
		Otherwise, we compute it via two aggregates (two queries) to avoid join double-counting.
		"""

		# If annotated on the queryset, it will exist in instance __dict__
		annotated = self.__dict__.get("total_asset_value")
		if isinstance(annotated, Decimal):
			return annotated

		site_total = (
			self.properties.aggregate(
				total=Coalesce(
					Sum("purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)["total"]
			or Decimal("0.00")
		)

		# Lazy import to avoid circular deps at import-time
		from apps.properties.models import Unit

		unit_total = (
			Unit.objects.filter(property__portfolio=self).aggregate(
				total=Coalesce(
					Sum("purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)["total"]
			or Decimal("0.00")
		)

		return site_total + unit_total