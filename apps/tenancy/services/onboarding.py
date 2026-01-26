from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django_tenants.utils import schema_context

from apps.tenancy.models import Domain, Tenant, TenantStatus

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


def ensure_tenant_admin_user(
	*,
	tenant: Tenant,
	admin_email: str,
	admin_password: str | None = None,
	admin_first_name: str | None = None,
	admin_last_name: str | None = None,
):
	"""
	Create/update a tenant-local superuser for the given tenant schema.

	- If `admin_password` is provided, it is set/updated.
	- Otherwise, a newly-created user is given an unusable password (so you can
	  drive password setup via a reset flow).
	"""
	admin_email = (admin_email or "").strip().lower()
	if not admin_email:
		raise ValidationError("admin_email is required to create the tenant admin user.")

	with schema_context(tenant.schema_name):
		User = get_user_model()
		u, created = User.objects.get_or_create(
			email=admin_email,
			defaults={"is_staff": True, "is_superuser": True},
		)
		u.is_staff = True
		u.is_superuser = True

		if admin_password:
			u.set_password(admin_password)
		elif created and u.has_usable_password():
			# Keep the user in a "set password" state; admin will generate a reset link.
			u.set_unusable_password()

		u.save()

		# Best-effort: attach a Contact so we can show initials/name in the UI.
		first = (admin_first_name or "").strip()
		last = (admin_last_name or "").strip()
		display_name = (f"{first} {last}".strip() if first or last else "")
		if display_name:
			try:
				from apps.contacts.models import Contact

				if not getattr(u, "contact_id", None):
					c = Contact.objects.filter(email__iexact=admin_email).first()
					if not c:
						c = Contact.objects.create(display_name=display_name, email=admin_email)
					u.contact = c
					u.save(update_fields=["contact"])
				else:
					# Keep contact name in sync if present
					if u.contact and not (u.contact.display_name or "").strip():
						u.contact.display_name = display_name
						u.contact.save(update_fields=["display_name", "updated_at"])
			except Exception:
				pass

		# If the user cannot log in yet, generate a one-time set-password link payload.
		if not u.has_usable_password():
			uidb64 = urlsafe_base64_encode(force_bytes(u.pk))
			token = default_token_generator.make_token(u)
			return {"uidb64": uidb64, "token": token, "email": admin_email}

	return None


def provision_tenant(
	*,
	tenant: Tenant,
	admin_email: str | None = None,
	admin_password: str | None = None,
	admin_first_name: str | None = None,
	admin_last_name: str | None = None,
):
	"""
	Creates schema (django-tenants via save) + migrates tenant schema.
	Optionally creates/updates a tenant-local admin user.

	Idempotent-ish: safe to re-run if tenant already provisioned.
	"""
	if tenant.status != TenantStatus.ACTIVE:
		tenant.status = TenantStatus.PROVISIONING
		tenant.save(update_fields=["status"])

		# Your CLI previously worked with: migrate_schemas --schema=acme
		call_command("migrate_schemas", schema=tenant.schema_name, interactive=False)

	reset_payload = None
	if admin_email:
		reset_payload = ensure_tenant_admin_user(
			tenant=tenant,
			admin_email=admin_email,
			admin_password=admin_password,
			admin_first_name=admin_first_name,
			admin_last_name=admin_last_name,
		)

	tenant.status = TenantStatus.ACTIVE
	tenant.save(update_fields=["status"])

	return reset_payload


def suspend_tenant(*, tenant: Tenant):
	tenant.status = TenantStatus.SUSPENDED
	tenant.save(update_fields=["status"])


def activate_tenant(*, tenant: Tenant):
	tenant.status = TenantStatus.ACTIVE
	tenant.save(update_fields=["status"])