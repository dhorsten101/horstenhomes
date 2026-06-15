from __future__ import annotations

from django.db import models

from apps.core.contact_linked import ContactLinkedRecordMixin
from apps.core.models import TimeStampedUUIDModel


class EstateAgent(ContactLinkedRecordMixin, TimeStampedUUIDModel):
	"""Estate agent (sales) linked to a contact."""

	name = models.CharField(max_length=200, db_index=True)
	contact = models.ForeignKey(
		"contacts.Contact",
		on_delete=models.PROTECT,
		related_name="estate_agents",
	)
	reference = models.CharField(max_length=120, blank=True, db_index=True, help_text="Agent or firm reference number.")
	notes = models.TextField(blank=True)
	is_active = models.BooleanField(default=True, db_index=True)

	class Meta:
		ordering = ("name",)
		indexes = [
			models.Index(fields=["is_active", "name"]),
		]

	def __str__(self) -> str:
		return self.name
