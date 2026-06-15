from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.leases.models import Lease, LeaseStatus
from apps.properties.models import Unit, UnitStatus

EXPIRING_LEASE_DAYS = 90


def active_leases_expiring_queryset(*, within_days: int = EXPIRING_LEASE_DAYS):
	"""Active fixed-term leases at or before the expiry window (includes overdue)."""
	today = timezone.localdate()
	return Lease.objects.filter(
		status=LeaseStatus.ACTIVE,
		end_date__isnull=False,
		end_date__lte=today + timedelta(days=within_days),
	)


def active_month_to_month_leases_queryset():
	"""Active leases with no fixed end date."""
	return Lease.objects.filter(status=LeaseStatus.ACTIVE, end_date__isnull=True)


def crm_occupancy_stats(*, expiring_within_days: int = EXPIRING_LEASE_DAYS) -> dict[str, int]:
	return {
		"empty_units": Unit.objects.filter(status=UnitStatus.VACANT).count(),
		"leases_expiring": active_leases_expiring_queryset(within_days=expiring_within_days).count(),
		"month_to_month_leases": active_month_to_month_leases_queryset().count(),
	}
