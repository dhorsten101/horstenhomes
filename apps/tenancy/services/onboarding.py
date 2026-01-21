from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import transaction

from apps.tenancy.models import Tenant, Domain, TenantStatus


RESERVED = {"public", "admin", "www", "api", "root", "static", "media"}


def validate_tenant_inputs(*, slug: str, domain: str):
	slug = (slug or "").strip().lower()
	if slug in RESERVED:
		raise ValidationError(f"Slug '{slug}' is reserved.")
	if domain and "://" in domain:
		raise ValidationError("Domain must be a hostname only (no scheme).")


@transaction.atomic
def create_tenant_record(*, name: str, slug: str, domain: str, is_primary=True) -> Tenant:
	validate_tenant_inputs(slug=slug, domain=domain)
	
	tenant = Tenant.objects.create(
		name=name,
		slug=slug,
		status=TenantStatus.PENDING,
	)
	Domain.objects.create(domain=domain, tenant=tenant, is_primary=is_primary)
	return tenant


def provision_tenant(*, tenant: Tenant):
	"""
	Creates schema (django-tenants via save) + migrates tenant schema.
	Idempotent-ish: safe to re-run if tenant already provisioned.
	"""
	if tenant.status == TenantStatus.ACTIVE:
		return
	
	tenant.status = TenantStatus.PROVISIONING
	tenant.save(update_fields=["status"])
	
	# Your CLI previously worked with: migrate_schemas --schema=acme
	call_command("migrate_schemas", schema=tenant.schema_name, interactive=False)
	
	tenant.status = TenantStatus.ACTIVE
	tenant.save(update_fields=["status"])


def suspend_tenant(*, tenant: Tenant):
	tenant.status = TenantStatus.SUSPENDED
	tenant.save(update_fields=["status"])


def activate_tenant(*, tenant: Tenant):
	tenant.status = TenantStatus.ACTIVE
	tenant.save(update_fields=["status"])