from __future__ import annotations

import os

from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedUUIDModel


def _public_listing_photo_upload_to(instance: PublicListingPhoto, filename: str) -> str:
	base, ext = os.path.splitext(filename)
	safe_base = slugify(base)[:80] or "photo"
	return f"public-listings/{instance.listing_id}/{safe_base}{ext.lower()}"


class PublicListing(TimeStampedUUIDModel):
	"""
	Rental listing on the public (www) site — not tied to tenant CRM units.
	Managed by staff via Django admin on the public schema.
	"""

	property_name = models.CharField(max_length=200)
	address_line1 = models.CharField(max_length=200, blank=True)
	address_city = models.CharField(max_length=120, blank=True)

	unit_number = models.CharField(max_length=60)
	bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
	bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
	size_m2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

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
		ordering = ("-updated_at",)
		indexes = [
			models.Index(fields=["is_published", "created_at"]),
		]

	@property
	def amenities_list(self) -> list[str]:
		return [item.strip() for item in (self.amenities or "").split(",") if item.strip()]

	@property
	def primary_photo(self) -> PublicListingPhoto | None:
		if hasattr(self, "_primary_photo"):
			return self._primary_photo
		photo = self.photos.filter(is_primary=True).order_by("sort_order", "created_at").first()
		if not photo:
			photo = self.photos.order_by("sort_order", "created_at").first()
		self._primary_photo = photo
		return photo

	def __str__(self) -> str:
		return f"{self.property_name} · {self.unit_number}: {self.title}"


class PublicListingPhoto(TimeStampedUUIDModel):
	listing = models.ForeignKey(PublicListing, on_delete=models.CASCADE, related_name="photos")
	image = models.FileField(upload_to=_public_listing_photo_upload_to)
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
