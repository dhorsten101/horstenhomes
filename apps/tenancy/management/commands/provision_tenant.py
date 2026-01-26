from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from apps.tenancy.services.onboarding import create_tenant_record, provision_tenant


class Command(BaseCommand):
	help = "Provision a tenant: create tenant + domain, migrate schema, create tenant admin user."
	
	
	def add_arguments(self, parser):
		parser.add_argument("--name", required=True)
		parser.add_argument("--slug", required=True)
		parser.add_argument("--domain", required=True)
		parser.add_argument("--admin-email", required=True)
		parser.add_argument("--admin-password", required=False)
	
	def handle(self, *args, **opts):
		name = (opts["name"] or "").strip()
		slug = (opts["slug"] or "").strip().lower()
		domain = (opts["domain"] or "").strip().lower()
		admin_email = (opts["admin_email"] or "").strip().lower()
		admin_password = (opts.get("admin_password") or "").strip()

		if not name or not slug or not domain or not admin_email:
			raise ValidationError("Missing required inputs: name, slug, domain, admin_email")

		tenant = create_tenant_record(name=name, slug=slug, domain=domain, is_primary=True)
		provision_tenant(
			tenant=tenant,
			admin_email=admin_email,
			admin_password=admin_password or None,
		)
		
		self.stdout.write(self.style.SUCCESS(
			f"Provisioned tenant schema={tenant.schema_name}, domain={domain}"
		))
