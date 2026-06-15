from __future__ import annotations

from django.db import models


class ContactLinkedRecordMixin:
	"""Display helpers for records backed by a contacts.Contact."""

	@property
	def email(self) -> str:
		return self.contact.email if self.contact_id else ""

	@property
	def phone(self) -> str:
		return self.contact.phone if self.contact_id else ""

	@property
	def address(self):
		return self.contact.address if self.contact_id else None


class ContactLinkedAgentQuerySet(models.QuerySet):
	def ordered_by_contact(self):
		return self.order_by("contact__display_name")

