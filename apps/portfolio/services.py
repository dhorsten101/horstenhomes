from __future__ import annotations

from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from apps.properties.models import Property, Unit

_asset_field = DecimalField(max_digits=14, decimal_places=2)
_zero = Value(Decimal("0.00"), output_field=_asset_field)


def total_asset_value() -> Decimal:
	"""Sum of all property and unit purchase prices across the tenant."""
	site_total = (
		Property.objects.aggregate(
			total=Coalesce(Sum("purchase_price"), _zero),
		)["total"]
		or Decimal("0.00")
	)
	unit_total = (
		Unit.objects.aggregate(
			total=Coalesce(Sum("purchase_price"), _zero),
		)["total"]
		or Decimal("0.00")
	)
	return site_total + unit_total
