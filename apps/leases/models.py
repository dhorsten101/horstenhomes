from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedUUIDModel


class LeaseStatus(models.TextChoices):
	DRAFT = "draft", "Draft"
	ACTIVE = "active", "Active"
	ENDED = "ended", "Ended"


class Lease(TimeStampedUUIDModel):
	"""
	Tenancy / lease agreement for a unit.
	"""

	unit = models.ForeignKey("properties.Unit", on_delete=models.PROTECT, related_name="leases")
	primary_tenant = models.ForeignKey("contacts.Contact", on_delete=models.PROTECT, related_name="leases")

	status = models.CharField(max_length=20, choices=LeaseStatus.choices, default=LeaseStatus.DRAFT, db_index=True)

	start_date = models.DateField(default=timezone.now, db_index=True)
	end_date = models.DateField(null=True, blank=True)

	rent_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	billing_day = models.PositiveSmallIntegerField(default=1)

	external_id = models.CharField(max_length=120, blank=True, db_index=True)
	source = models.CharField(max_length=80, blank=True)  # "manual", "csv", "api:xyz"

	class Meta:
		indexes = [
			models.Index(fields=["unit", "status"]),
			models.Index(fields=["primary_tenant", "status"]),
			# Common listing/query patterns
			models.Index(fields=["unit", "created_at"]),
			models.Index(fields=["primary_tenant", "created_at"]),
			models.Index(fields=["status", "created_at"]),
		]

	def __str__(self) -> str:
		return f"{self.unit} ({self.status})"