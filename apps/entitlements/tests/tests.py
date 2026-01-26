from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from apps.entitlements.models import Plan, TenantPlan
from apps.entitlements.services import (
	QUOTA_MAX_STORAGE_BYTES,
	QUOTA_MAX_UNITS,
	USAGE_STORAGE_BYTES,
	add_storage_bytes,
	check_quota,
	get_effective_quota_limit,
	increment_usage,
)
from apps.tenancy.models import Tenant

try:
	from django_tenants.utils import schema_context
except Exception:  # pragma: no cover
	schema_context = None


class EntitlementsServicesTests(TestCase):
	def setUp(self):
		if schema_context is None:
			self.skipTest("django-tenants not available")

		with schema_context("public"):
			self.tenant = Tenant.objects.create(name="Acme", slug="acme", schema_name="acme")
			self.plan = Plan.objects.create(code="starter", name="Starter", quotas={QUOTA_MAX_UNITS: 2})
			TenantPlan.objects.create(tenant=self.tenant, plan=self.plan)

	def test_get_effective_quota_limit_reads_plan(self):
		limit = get_effective_quota_limit(self.tenant, QUOTA_MAX_UNITS)
		self.assertEqual(limit, 2)

	def test_check_quota_soft_allows_when_under_limit(self):
		qc = check_quota(self.tenant, key=QUOTA_MAX_UNITS, used=1, needed=1)
		self.assertTrue(qc.allowed)
		self.assertEqual(qc.remaining, 1)

	@override_settings(ENTITLEMENTS_ENFORCEMENT="hard")
	def test_check_quota_hard_blocks_when_over_limit(self):
		qc = check_quota(self.tenant, key=QUOTA_MAX_UNITS, used=2, needed=1)
		self.assertFalse(qc.allowed)
		self.assertEqual(qc.limit, 2)

	def test_increment_usage_creates_and_increments_counter(self):
		with schema_context("public"):
			v1 = increment_usage(self.tenant, key="api_requests", delta=1, period="day")
			v2 = increment_usage(self.tenant, key="api_requests", delta=2, period="day")
		self.assertEqual(v1, 1)
		self.assertEqual(v2, 3)

	@override_settings(ENTITLEMENTS_ENFORCEMENT="hard")
	def test_storage_quota_blocks_in_hard_mode(self):
		with schema_context("public"):
			self.plan.quotas = {QUOTA_MAX_STORAGE_BYTES: 10}
			self.plan.save(update_fields=["quotas"])

		with self.assertRaises(ValidationError):
			add_storage_bytes(self.tenant, 20, metadata={"source": "test"})

	def test_storage_quota_tracks_usage_key(self):
		with schema_context("public"):
			self.plan.quotas = {QUOTA_MAX_STORAGE_BYTES: 1000}
			self.plan.save(update_fields=["quotas"])
			add_storage_bytes(self.tenant, 123, metadata={"source": "test"})
			# counter is stored under usage key (not max_storage_bytes)
			from apps.entitlements.models import QuotaUsage

			self.assertTrue(
				QuotaUsage.objects.filter(tenant=self.tenant, key=USAGE_STORAGE_BYTES).exists()
			)
