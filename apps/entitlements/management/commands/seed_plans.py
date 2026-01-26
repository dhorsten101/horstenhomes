from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.entitlements.models import Plan
from apps.entitlements.services import QUOTA_MAX_UNITS


class Command(BaseCommand):
	help = "Create/update default subscription plans (provider-agnostic)."

	def handle(self, *args, **options):
		plans = [
			{
				"code": "free",
				"name": "Free",
				"description": "Up to 25 units included.",
				"currency": "USD",
				"unit_price": Decimal("0.00"),
				"included_units": 25,
				"quotas": {QUOTA_MAX_UNITS: 25},
			},
			{
				"code": "unlimited",
				"name": "Unlimited",
				"description": "Unlimited units.",
				"currency": "USD",
				"unit_price": Decimal("25.00"),
				# Unlimited: omit max_units so it is treated as "no limit".
				"included_units": 0,
				"quotas": {},
			},
		]

		for p in plans:
			obj, created = Plan.objects.update_or_create(
				code=p["code"],
				defaults={
					"name": p["name"],
					"description": p["description"],
					"is_active": True,
					"currency": p["currency"],
					"unit_price": p["unit_price"],
					"included_units": p["included_units"],
					"feature_flags": {"crm": True},
					"quotas": p["quotas"],
				},
			)
			self.stdout.write(f"{'Created' if created else 'Updated'} plan {obj.code}")

		# Deactivate plans not in the seeded set (keeps history but removes from pricing/assignment).
		active_codes = {p["code"] for p in plans}
		deactivated = Plan.objects.exclude(code__in=active_codes).filter(is_active=True).update(is_active=False)
		if deactivated:
			self.stdout.write(f"Deactivated {deactivated} plan(s)")

