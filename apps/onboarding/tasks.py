from __future__ import annotations

import logging

from celery import shared_task

try:
	from django_tenants.utils import schema_context
except Exception:  # pragma: no cover
	schema_context = None

from apps.entitlements.services import ensure_tenant_plan
from apps.tenancy.models import Tenant
from apps.tenancy.services.onboarding import create_tenant_record, provision_tenant, validate_tenant_inputs

from .models import TenantRequest, TenantRequestStatus

log = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def auto_provision_free_tenant(self, *, tenant_request_uid: str) -> None:
	"""
	Auto-provision a free-plan tenant in the background.
	This replaces ad-hoc threading and gives retries + visibility.
	"""
	if schema_context is None:
		return

	with schema_context("public"):
		tr = TenantRequest.objects.filter(uid=tenant_request_uid).first()
		if not tr:
			return
		if tr.status == TenantRequestStatus.PROVISIONED:
			return

		slug = (tr.desired_slug or "").strip().lower()
		if not slug:
			return

		base_domain = "horstenhomes.local"
		try:
			from django.conf import settings

			base_domain = getattr(settings, "BASE_TENANT_DOMAIN", base_domain)
		except Exception:
			pass

		domain = f"{slug}.{base_domain}"
		validate_tenant_inputs(slug=slug, domain=domain)

		# Avoid duplicates
		if Tenant.objects.filter(schema_name=slug).exists():
			return

		tenant = create_tenant_record(name=tr.company_name, slug=slug, domain=domain, is_primary=True)
		ensure_tenant_plan(tenant, plan_code=(tr.requested_plan_code or "free"))

	reset_payload = provision_tenant(
		tenant=tenant,
		admin_email=(tr.admin_email or tr.contact_email or "").strip().lower(),
		admin_first_name=(tr.contact_first_name or ""),
		admin_last_name=(tr.contact_last_name or ""),
	)

	with schema_context("public"):
		tr = TenantRequest.objects.filter(uid=tenant_request_uid).first()
		if not tr:
			return
		tr.status = TenantRequestStatus.PROVISIONED
		tr.converted_tenant_schema = tenant.schema_name
		tr.provisioned_domain = domain
		if reset_payload:
			tr.reset_uidb64 = reset_payload.get("uidb64", "") or ""
			tr.reset_token = reset_payload.get("token", "") or ""
		tr.save(
			update_fields=[
				"status",
				"converted_tenant_schema",
				"provisioned_domain",
				"reset_uidb64",
				"reset_token",
				"updated_at",
			]
		)

	log.info("Auto-provisioned tenant=%s domain=%s tr=%s", slug, domain, tenant_request_uid)

