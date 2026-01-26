from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedUUIDModel


class Plan(TimeStampedUUIDModel):
	"""
	A subscription plan definition (stored in PUBLIC schema).

	Quotas are stored as JSON for flexibility at early stage; keys should be stable,
	e.g.:
	  - max_users
	  - max_units   (billing driver in this product)
	  - max_storage_bytes
	  - api_requests_per_day
	"""

	code = models.SlugField(unique=True)  # e.g. "starter", "pro"
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True, db_index=True)

	# Billing primitives (provider-agnostic)
	currency = models.CharField(max_length=3, default="USD")
	unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	included_units = models.PositiveIntegerField(default=0)

	feature_flags = models.JSONField(default=dict, blank=True)  # {"crm": true, "api": false}
	quotas = models.JSONField(default=dict, blank=True)  # {"max_units": 100, "max_users": 10}

	class Meta:
		indexes = [
			models.Index(fields=["is_active", "created_at"]),
		]

	def __str__(self) -> str:
		return f"{self.name} ({self.code})"


class FeatureFlag(TimeStampedUUIDModel):
	"""
	Defines a stable feature key, used by plans and tenant overrides.
	"""

	key = models.SlugField(unique=True)  # e.g. "crm", "api", "billing"
	description = models.CharField(max_length=250, blank=True)
	default_enabled = models.BooleanField(default=False)

	def __str__(self) -> str:
		return self.key


class TenantPlanStatus(models.TextChoices):
	ACTIVE = "active", "Active"
	TRIAL = "trial", "Trial"
	CANCELED = "canceled", "Canceled"
	PAST_DUE = "past_due", "Past due"


class TenantPlan(TimeStampedUUIDModel):
	"""
	Associates a tenant with a plan (stored in PUBLIC schema).

	Overrides allow special cases without multiplying plan definitions.
	"""

	tenant = models.OneToOneField("tenancy.Tenant", on_delete=models.CASCADE, related_name="tenant_plan")
	plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="tenant_plans")
	status = models.CharField(max_length=20, choices=TenantPlanStatus.choices, default=TenantPlanStatus.ACTIVE, db_index=True)

	starts_at = models.DateTimeField(default=timezone.now)
	ends_at = models.DateTimeField(null=True, blank=True)

	feature_overrides = models.JSONField(default=dict, blank=True)  # {"api": true}
	quota_overrides = models.JSONField(default=dict, blank=True)  # {"max_units": 250}

	def __str__(self) -> str:
		return f"{self.tenant.slug}: {self.plan.code} ({self.status})"


class QuotaUsage(TimeStampedUUIDModel):
	"""
	Usage counters (stored in PUBLIC schema).

	The period model supports daily/monthly windows:
	  - key="api_requests", period="day"
	  - key="storage_bytes", period="month"
	"""

	tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="quota_usages")
	key = models.SlugField(db_index=True)  # "max_units" usage can be derived, but keep generic counters here

	period = models.CharField(max_length=20, default="month", db_index=True)  # day|month|lifetime
	period_start = models.DateTimeField(default=timezone.now, db_index=True)
	period_end = models.DateTimeField(null=True, blank=True)

	value = models.BigIntegerField(default=0)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "key", "period", "period_start"], name="entitlements_quota_unique_window"),
		]
		indexes = [
			models.Index(fields=["tenant", "key", "period", "period_start"]),
		]

	def __str__(self) -> str:
		return f"{self.tenant.slug} {self.key}={self.value} ({self.period})"
