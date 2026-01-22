from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audits.models import AuditEvent

try:
	from django_tenants.utils import schema_context
except Exception:  # pragma: no cover
	schema_context = None


class Command(BaseCommand):
	help = "Purge old audit events (retention). Uses hard delete."

	def add_arguments(self, parser):
		parser.add_argument("--days", type=int, default=90, help="Delete events older than N days (default: 90).")
		parser.add_argument(
			"--all-tenants",
			action="store_true",
			help="If run from public schema, purge public + all tenant schemas.",
		)

	def handle(self, *args, **opts):
		days = int(opts["days"])
		cutoff = timezone.now() - timedelta(days=days)

		def purge_current_schema(label: str):
			count = AuditEvent.objects.filter(created_at__lt=cutoff).count()
			deleted = AuditEvent.objects.filter(created_at__lt=cutoff).hard_delete()
			self.stdout.write(f"{label}: deleted {count} events (hard_delete={deleted}).")

		all_tenants = bool(opts["all_tenants"])
		if not all_tenants:
			purge_current_schema("current schema")
			return

		if schema_context is None:
			raise RuntimeError("django-tenants not available; cannot use --all-tenants.")

		# Avoid importing Tenant model at module import time.
		from apps.tenancy.models import Tenant

		# Always purge public first
		with schema_context("public"):
			purge_current_schema("public")
			tenants = list(Tenant.objects.exclude(schema_name="public").values_list("schema_name", flat=True))

		for schema_name in tenants:
			with schema_context(schema_name):
				purge_current_schema(schema_name)

