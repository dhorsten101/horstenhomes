from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Contractor(TimeStampedUUIDModel):
	"""Trade or maintenance contractor."""

	name = models.CharField(max_length=200, db_index=True)
	trade = models.CharField(max_length=120, blank=True, db_index=True, help_text="e.g. plumbing, electrical")
	email = models.EmailField(blank=True, db_index=True)
	phone = models.CharField(max_length=60, blank=True, db_index=True)
	reference = models.CharField(max_length=120, blank=True, db_index=True, help_text="Contractor reference number.")
	notes = models.TextField(blank=True)

	address = models.ForeignKey(
		"addresses.Address",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="contractors",
	)
	contacts = models.ManyToManyField(
		"contacts.Contact",
		blank=True,
		related_name="contractors",
		help_text="People linked to this contractor.",
	)

	is_active = models.BooleanField(default=True, db_index=True)

	class Meta:
		ordering = ("name",)
		indexes = [
			models.Index(fields=["is_active", "name"]),
			models.Index(fields=["trade", "name"]),
		]

	def __str__(self) -> str:
		return self.name
