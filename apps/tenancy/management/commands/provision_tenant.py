from django.core.management.base import BaseCommand
from django.core.management import call_command
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model

from apps.tenancy.models import Tenant, Domain
import re


class Command(BaseCommand):
	help = "Provision a tenant: create tenant + domain, migrate schema, create tenant admin user."
	
	
	def add_arguments(self, parser):
		parser.add_argument("--name", required=True)
		parser.add_argument("--slug", required=True)
		parser.add_argument("--domain", required=True)
		parser.add_argument("--admin-email", required=True)
		parser.add_argument("--admin-password", required=True)
	
	def handle(self, *args, **opts):
		slug = opts["slug"].lower().strip()
		schema_name = re.sub(r"[^a-z0-9_]", "_", slug)
		
		tenant = Tenant.objects.create(
			name=opts["name"],
			slug=slug,
			schema_name=schema_name,)
		# tenant = Tenant.objects.create(name=opts["name"], slug=opts["slug"])
		Domain.objects.create(domain=opts["domain"], tenant=tenant, is_primary=True)
		
		call_command("migrate_schemas", schema_name=tenant.schema_name, interactive=False, verbosity=1)
		
		with schema_context(tenant.schema_name):
			User = get_user_model()
			User.objects.create_superuser(opts["admin_email"], opts["admin_password"])
		
		self.stdout.write(self.style.SUCCESS(
			f"Provisioned tenant schema={tenant.schema_name}, domain={opts['domain']}"
		))
		