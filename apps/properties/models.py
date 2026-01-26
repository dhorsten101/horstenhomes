from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedUUIDModel


class PropertyType(models.TextChoices):
	RESIDENTIAL = "residential", "Residential"
	COMMERCIAL = "commercial", "Commercial"
	MIXED = "mixed", "Mixed use"


class UnitStatus(models.TextChoices):
	VACANT = "vacant", "Vacant"
	OCCUPIED = "occupied", "Occupied"
	OFFLINE = "offline", "Offline"


class Property(TimeStampedUUIDModel):
	portfolio = models.ForeignKey("portfolio.Portfolio", on_delete=models.PROTECT, related_name="properties")

	name = models.CharField(max_length=200, db_index=True)
	property_type = models.CharField(max_length=20, choices=PropertyType.choices, db_index=True)

	purchase_date = models.DateField(null=True, blank=True, db_index=True)
	previous_purchase_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
	purchase_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

	address = models.ForeignKey(
		"addresses.Address",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="properties",
	)

	external_id = models.CharField(max_length=120, blank=True, db_index=True)
	source = models.CharField(max_length=80, blank=True)  # "manual", "csv", "api:xyz"

	is_archived = models.BooleanField(default=False, db_index=True)

	class Meta:
		indexes = [
			models.Index(fields=["portfolio", "created_at"]),
			models.Index(fields=["property_type", "created_at"]),
		]

	def __str__(self) -> str:
		return self.name


class Unit(TimeStampedUUIDModel):
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="units")

	unit_number = models.CharField(max_length=60, db_index=True)
	floor = models.CharField(max_length=20, blank=True)
	bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
	bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
	size_m2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

	# Value/cost basis of this unit (apartment purchase price OR build cost).
	purchase_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

	status = models.CharField(max_length=20, choices=UnitStatus.choices, default=UnitStatus.VACANT, db_index=True)

	external_id = models.CharField(max_length=120, blank=True, db_index=True)
	source = models.CharField(max_length=80, blank=True)  # "manual", "csv", "api:xyz"

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=("property", "unit_number"), name="properties_unit_unique_per_property"),
		]
		indexes = [
			models.Index(fields=["property", "status"]),
			# Common listing/query patterns
			models.Index(fields=["property", "created_at"]),
			models.Index(fields=["status", "created_at"]),
		]

	def __str__(self) -> str:
		return f"{self.property}: {self.unit_number}"