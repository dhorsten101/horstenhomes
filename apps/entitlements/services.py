from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from apps.audits.models import AuditStatus
from apps.audits.services import audit_log
from apps.entitlements.models import QuotaUsage, TenantPlan
from apps.tenancy.models import Tenant

try:
	from django_tenants.utils import schema_context
except Exception:  # pragma: no cover
	schema_context = None

log = logging.getLogger(__name__)


QUOTA_MAX_USERS = "max_users"
QUOTA_MAX_UNITS = "max_units"
QUOTA_MAX_STORAGE_BYTES = "max_storage_bytes"
QUOTA_API_REQUESTS_PER_DAY = "api_requests_per_day"

# Usage counters (separate from quota keys so you can change limits later without
# having to rename stored counters)
USAGE_STORAGE_BYTES = "storage_bytes"


def ensure_tenant_plan(tenant: Tenant, *, plan_code: str = "free") -> TenantPlan | None:
	"""
	Ensure a tenant has a TenantPlan row (PUBLIC schema).
	Used for auto-provisioning (e.g. defaulting new tenants to the free plan).
	"""
	if schema_context is None:
		return None
	plan_code = (plan_code or "free").strip().lower()
	with schema_context("public"):
		from apps.entitlements.models import Plan

		plan = Plan.objects.filter(code=plan_code, is_active=True).first()
		if not plan:
			return None
		tp, _ = TenantPlan.objects.get_or_create(
			tenant=tenant,
			defaults={"plan": plan, "status": "active"},
		)
		if tp.plan_id != plan.id:
			tp.plan = plan
			tp.save(update_fields=["plan", "updated_at"])
		return tp


def _utc_now() -> datetime:
	return datetime.now(tz=UTC)


def _window_start(period: str, now: datetime) -> datetime:
	if period == "day":
		return now.replace(hour=0, minute=0, second=0, microsecond=0)
	if period == "month":
		return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	return now.replace(microsecond=0)


def _window_end(period: str, start: datetime) -> datetime | None:
	if period == "day":
		return start + timedelta(days=1)
	if period == "month":
		if start.month == 12:
			return start.replace(year=start.year + 1, month=1)
		return start.replace(month=start.month + 1)
	return None


def _enforcement_mode() -> str:
	return (getattr(settings, "ENTITLEMENTS_ENFORCEMENT", "soft") or "soft").strip().lower()


def get_current_tenant_plan(tenant) -> TenantPlan | None:
	"""
	Read tenant plan from PUBLIC schema.
	"""
	if schema_context is None:
		return None
	with schema_context("public"):
		return TenantPlan.objects.select_related("plan", "tenant").filter(tenant_id=tenant.id).first()


def get_tenant_by_schema(schema_name: str) -> Tenant | None:
	"""
	Resolve a tenant row from PUBLIC schema by schema_name.
	"""
	if schema_context is None:
		return None
	schema_name = (schema_name or "").strip()
	if not schema_name or schema_name == "public":
		return None
	with schema_context("public"):
		return Tenant.objects.filter(schema_name=schema_name).first()


def get_effective_quota_limit(tenant, key: str) -> int | None:
	"""
	Returns:
	  - None => no limit configured (treat as unlimited)
	  - >= 0 => limit
	"""
	tp = get_current_tenant_plan(tenant)
	if not tp:
		return None

	limit = None
	try:
		limit = (tp.plan.quotas or {}).get(key)
	except Exception:
		limit = None

	try:
		if key in (tp.quota_overrides or {}):
			limit = tp.quota_overrides.get(key)
	except Exception:
		pass

	if limit is None:
		return None
	try:
		return int(limit)
	except Exception:
		return None


def is_feature_enabled(tenant, key: str) -> bool:
	tp = get_current_tenant_plan(tenant)
	if not tp:
		return False
	val = False
	try:
		val = bool((tp.plan.feature_flags or {}).get(key, False))
	except Exception:
		val = False
	try:
		if key in (tp.feature_overrides or {}):
			val = bool(tp.feature_overrides.get(key))
	except Exception:
		pass
	return val


def get_usage_counter(tenant, key: str, period: str = "month") -> QuotaUsage:
	if schema_context is None:
		raise RuntimeError("schema_context unavailable")

	now = _utc_now()
	start = _window_start(period, now)
	end = _window_end(period, start)

	with schema_context("public"):
		obj, _ = QuotaUsage.objects.get_or_create(
			tenant_id=tenant.id,
			key=key,
			period=period,
			period_start=start,
			defaults={"period_end": end, "value": 0},
		)
		return obj


@dataclass(frozen=True)
class QuotaCheck:
	key: str
	limit: int | None
	used: int
	needed: int
	allowed: bool
	mode: str

	@property
	def remaining(self) -> int | None:
		if self.limit is None:
			return None
		return max(self.limit - self.used, 0)


def check_quota(tenant, key: str, used: int, needed: int = 1) -> QuotaCheck:
	limit = get_effective_quota_limit(tenant, key)
	mode = _enforcement_mode()
	if limit is None:
		return QuotaCheck(key=key, limit=None, used=used, needed=needed, allowed=True, mode=mode)
	return QuotaCheck(key=key, limit=limit, used=used, needed=needed, allowed=(used + needed) <= limit, mode=mode)


def enforce_quota(
	tenant,
	*,
	key: str,
	used: int,
	needed: int = 1,
	action: str,
	obj=None,
	metadata: dict[str, Any] | None = None,
) -> QuotaCheck:
	qc = check_quota(tenant, key=key, used=used, needed=needed)
	if qc.allowed:
		return qc

	payload: dict[str, Any] = {
		"tenant_schema": getattr(tenant, "schema_name", ""),
		"tenant_slug": getattr(tenant, "slug", ""),
		"key": key,
		"used": used,
		"needed": needed,
		"limit": qc.limit,
		"mode": qc.mode,
	}
	if metadata:
		payload.update(metadata)

	try:
		audit_log(
			action=action,
			obj=obj,
			status=AuditStatus.FAILURE,
			message=f"Quota exceeded: {key} (used={used}, needed={needed}, limit={qc.limit})",
			metadata=payload,
			tenant_schema="public",
			defer=False,
		)
	except Exception:
		pass

	log.warning("Quota exceeded: %s", payload)

	if qc.mode == "hard":
		raise ValidationError(f"Quota exceeded: {key}")
	return qc


def increment_usage(tenant, key: str, delta: int = 1, period: str = "month") -> int:
	"""
	Generic usage incrementer (PUBLIC schema).
	Returns the new value.
	"""
	if schema_context is None:
		raise RuntimeError("schema_context unavailable")

	counter = get_usage_counter(tenant, key=key, period=period)
	with schema_context("public"):
		with transaction.atomic():
			QuotaUsage.objects.filter(pk=counter.pk).update(value=F("value") + int(delta))
			counter.refresh_from_db(fields=["value"])
			return int(counter.value)


def increment_and_enforce(
	tenant,
	*,
	key: str,
	period: str,
	action: str,
	obj=None,
	metadata: dict[str, Any] | None = None,
	delta: int = 1,
) -> int:
	"""
	Atomic (PUBLIC schema):
	- lock usage row
	- check limit
	- increment if allowed
	"""
	if schema_context is None:
		raise RuntimeError("schema_context unavailable")

	limit = get_effective_quota_limit(tenant, key)
	mode = _enforcement_mode()
	counter = get_usage_counter(tenant, key=key, period=period)

	with schema_context("public"):
		with transaction.atomic():
			locked = QuotaUsage.objects.select_for_update().get(pk=counter.pk)
			used = int(locked.value or 0)
			needed = int(delta)

			if limit is not None and (used + needed) > int(limit):
				enforce_quota(
					tenant,
					key=key,
					used=used,
					needed=needed,
					action=action,
					obj=obj,
					metadata=metadata,
				)
				# soft mode falls through (records audit/log), still increment for tracking.
				if mode == "hard":
					return used

			locked.value = used + needed
			locked.save(update_fields=["value", "updated_at"])
			return int(locked.value)


def add_storage_bytes(tenant, delta_bytes: int, *, metadata: dict[str, Any] | None = None) -> int:
	"""
	Record storage usage (PUBLIC schema) and enforce `max_storage_bytes`.

	Call this from any upload endpoint once you know the final stored size.
	"""
	delta = int(delta_bytes)
	if delta <= 0:
		return 0

	# Atomic: enforce + increment together on the usage counter row
	if schema_context is None:
		raise RuntimeError("schema_context unavailable")

	mode = _enforcement_mode()
	limit = get_effective_quota_limit(tenant, QUOTA_MAX_STORAGE_BYTES)
	counter = get_usage_counter(tenant, key=USAGE_STORAGE_BYTES, period="month")

	with schema_context("public"):
		with transaction.atomic():
			locked = QuotaUsage.objects.select_for_update().get(pk=counter.pk)
			used = int(locked.value or 0)

			if limit is not None and (used + delta) > int(limit):
				enforce_quota(
					tenant,
					key=QUOTA_MAX_STORAGE_BYTES,
					used=used,
					needed=delta,
					action="quota.max_storage_bytes.exceeded",
					obj=None,
					metadata={**(metadata or {}), "delta_bytes": delta, "usage_key": USAGE_STORAGE_BYTES},
				)
				if mode == "hard":
					return used

			locked.value = used + delta
			locked.save(update_fields=["value", "updated_at"])
			return int(locked.value)
