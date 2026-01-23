from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Contact(TimeStampedUUIDModel):
	"""
	Generic contact record (people or businesses).
	"""

	display_name = models.CharField(max_length=200, db_index=True)
	email = models.EmailField(blank=True, db_index=True)
	phone = models.CharField(max_length=60, blank=True, db_index=True)

	address = models.ForeignKey(
		"addresses.Address",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="contacts",
	)

	external_id = models.CharField(max_length=120, blank=True, db_index=True)
	source = models.CharField(max_length=80, blank=True)  # "manual", "csv", "api:xyz"

	class Meta:
		indexes = [
			models.Index(fields=["email", "created_at"]),
			models.Index(fields=["phone", "created_at"]),
		]

	def __str__(self) -> str:
		return self.display_name