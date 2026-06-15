from __future__ import annotations

import os

from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedUUIDModel


class PropertyType(models.TextChoices):
	RESIDENTIAL = "residential", "Residential"
	COMMERCIAL = "commercial", "Commercial"
	MIXED = "mixed", "Mixed use"


class UnitStatus(models.TextChoices):
	VACANT = "vacant", "Vacant"
	OCCUPIED = "occupied", "Occupied"
	OFFLINE = "offline", "Offline"


def _listing_photo_upload_to(instance: ListingPhoto, filename: str) -> str:
	base, ext = os.path.splitext(filename)
	safe_base = slugify(base)[:80] or "photo"
	return f"listing-photos/{instance.listing_id}/{safe_base}{ext.lower()}"


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
	purchase_date = models.DateField(null=True, blank=True, db_index=True)
	purchase_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

	status = models.CharField(max_length=20, choices=UnitStatus.choices, default=UnitStatus.VACANT, db_index=True)

	external_id = models.CharField(max_length=120, blank=True, db_index=True)
	source = models.CharField(max_length=80, blank=True)  # "manual", "csv", "api:xyz"

	municipal_reference = models.CharField(
		max_length=120,
		blank=True,
		help_text="Municipal account or reference number for this unit.",
	)
	managing_agent_reference = models.CharField(
		max_length=120,
		blank=True,
		help_text="Managing agent account or reference for this unit.",
	)

	estate_agent = models.ForeignKey(
		"estate_agents.EstateAgent",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="units",
	)
	managing_agent = models.ForeignKey(
		"managing_agents.ManagingAgent",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="units",
	)
	rental_agent = models.ForeignKey(
		"rental_agents.RentalAgent",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="units",
	)

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


class UnitListing(TimeStampedUUIDModel):
	unit = models.OneToOneField(Unit, on_delete=models.CASCADE, related_name="listing")

	title = models.CharField(max_length=200)
	summary = models.TextField(blank=True)

	rent_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	available_from = models.DateField(null=True, blank=True)
	lease_term_months = models.PositiveSmallIntegerField(null=True, blank=True)
	furnished = models.BooleanField(default=False)
	pet_policy = models.CharField(max_length=120, blank=True)
	parking_spaces = models.PositiveSmallIntegerField(null=True, blank=True)
	utilities_included = models.CharField(max_length=120, blank=True)

	is_published = models.BooleanField(default=False, db_index=True)

	contact_email = models.EmailField(blank=True)
	contact_phone = models.CharField(max_length=40, blank=True)

	amenities = models.CharField(max_length=250, blank=True, help_text="Comma-separated list")

	class Meta:
		indexes = [
			models.Index(fields=["is_published", "created_at"]),
		]

	@property
	def amenities_list(self) -> list[str]:
		return [item.strip() for item in (self.amenities or "").split(",") if item.strip()]

	@property
	def primary_photo(self) -> ListingPhoto | None:
		if hasattr(self, "_primary_photo"):
			return self._primary_photo
		photo = self.photos.filter(is_primary=True).order_by("sort_order", "created_at").first()
		if not photo:
			photo = self.photos.order_by("sort_order", "created_at").first()
		self._primary_photo = photo
		return photo

	def __str__(self) -> str:
		state = "Published" if self.is_published else "Draft"
		return f"{self.unit} ({state})"


class ListingPhoto(TimeStampedUUIDModel):
	listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE, related_name="photos")
	image = models.FileField(upload_to=_listing_photo_upload_to)
	caption = models.CharField(max_length=200, blank=True)
	sort_order = models.PositiveSmallIntegerField(default=0)
	is_primary = models.BooleanField(default=False, db_index=True)

	class Meta:
		ordering = ["-is_primary", "sort_order", "created_at"]
		indexes = [
			models.Index(fields=["listing", "is_primary"]),
		]

	def __str__(self) -> str:
		return f"{self.listing} photo"