from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Address(TimeStampedUUIDModel):
	"""
	Generic postal address. Stored per-tenant (and also in public if you want to
	reuse for platform-level contacts).
	"""

	label = models.CharField(max_length=120, blank=True)  # e.g. "Head office"
	line1 = models.CharField(max_length=200)
	line2 = models.CharField(max_length=200, blank=True)
	city = models.CharField(max_length=120, blank=True, db_index=True)
	region = models.CharField(max_length=120, blank=True)  # state/province
	postal_code = models.CharField(max_length=40, blank=True)
	country = models.CharField(max_length=2, blank=True)  # ISO 3166-1 alpha-2

	lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

	class Meta:
		indexes = [
			models.Index(fields=["city", "created_at"]),
		]

	def __str__(self) -> str:
		parts = [self.line1]
		if self.city:
			parts.append(self.city)
		if self.country:
			parts.append(self.country)
		return ", ".join(parts)