from __future__ import annotations

from django.db import models

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