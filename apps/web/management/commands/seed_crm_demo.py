from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django_tenants.utils import schema_context

from apps.accounting.models import UnitExpense, UnitInvoice
from apps.contacts.models import Contact
from apps.contractors.models import Contractor
from apps.leases.models import Lease, LeaseStatus
from apps.portfolio.models import Portfolio
from apps.properties.models import Property, PropertyType, Unit, UnitStatus
from apps.tenancy.models import Tenant


def _subtract_months(d: date, months: int) -> date:
	year = d.year
	month = d.month - months
	while month <= 0:
		month += 12
		year -= 1
	return date(year, month, 1)


class Command(BaseCommand):
	help = "Seed demo CRM data (contacts, properties, units, leases, contractors, 24+ months of P&L)."

	def add_arguments(self, parser):
		parser.add_argument(
			"--schema",
			default="horstenhomes",
			help="Tenant schema name (default: horstenhomes)",
		)
		parser.add_argument(
			"--months",
			type=int,
			default=28,
			help="Months of invoice/expense history to generate (default: 28)",
		)
		parser.add_argument(
			"--clear-accounting",
			action="store_true",
			help="Delete all invoices and expenses before seeding accounting data",
		)

	def handle(self, *args, **options):
		schema = (options["schema"] or "").strip()
		months = max(int(options["months"]), 24)
		if not Tenant.objects.filter(schema_name=schema).exists():
			raise CommandError(f"Unknown tenant schema: {schema}")

		with schema_context(schema):
			with transaction.atomic():
				stats = self._seed(months=months, clear_accounting=options["clear_accounting"])

		self.stdout.write(self.style.SUCCESS(f"Seeded demo data on schema={schema}"))
		for key, val in stats.items():
			self.stdout.write(f"  {key}: {val}")

	def _seed(self, *, months: int, clear_accounting: bool) -> dict[str, int]:
		rng = random.Random(42)
		stats: dict[str, int] = {}

		contacts = self._ensure_contacts(rng)
		stats["contacts"] = Contact.objects.count()

		portfolios = self._ensure_portfolios(contacts, rng)
		stats["portfolios"] = Portfolio.objects.count()

		units = self._ensure_properties_and_units(portfolios, rng)
		stats["properties"] = Property.objects.count()
		stats["units"] = Unit.objects.count()

		stats["leases_created"] = self._ensure_leases(units, contacts, rng)
		stats["leases"] = Lease.objects.count()

		stats["contractors_created"] = self._ensure_contractors(contacts, rng)
		stats["contractors"] = Contractor.objects.count()

		if clear_accounting:
			UnitInvoice.objects.all().delete()
			UnitExpense.objects.all().delete()

		inv_n, exp_n = self._seed_accounting(units, months=months, rng=rng)
		stats["invoices_created"] = inv_n
		stats["expenses_created"] = exp_n
		stats["invoices"] = UnitInvoice.objects.count()
		stats["expenses"] = UnitExpense.objects.count()

		return stats

	def _ensure_contacts(self, rng: random.Random) -> list[Contact]:
		names = [
			("Thabo Mokoena", "thabo.mokoena@example.com", "082 100 1001"),
			("Sarah van der Merwe", "sarah.vdm@example.com", "082 100 1002"),
			("James Ndlovu", "james.ndlovu@example.com", "082 100 1003"),
			("Priya Pillay", "priya.pillay@example.com", "082 100 1004"),
			("Michael Botha", "michael.botha@example.com", "082 100 1005"),
			("Lerato Khumalo", "lerato.khumalo@example.com", "082 100 1006"),
			("Chris Williams", "chris.williams@example.com", "082 100 1007"),
			("Aisha Patel", "aisha.patel@example.com", "082 100 1008"),
			("David Fourie", "david.fourie@example.com", "082 100 1009"),
			("Nomsa Dlamini", "nomsa.dlamini@example.com", "082 100 1010"),
			("PlumbRight Ops", "ops@plumbright.demo", "011 555 0101"),
			("Spark Electrical", "admin@sparkelect.demo", "011 555 0202"),
		]
		contacts: list[Contact] = list(Contact.objects.all())
		for display_name, email, phone in names:
			obj, _ = Contact.objects.get_or_create(
				email=email,
				defaults={"display_name": display_name, "phone": phone, "source": "demo"},
			)
			if obj not in contacts:
				contacts.append(obj)
		rng.shuffle(contacts)
		return contacts

	def _ensure_portfolios(self, contacts: list[Contact], rng: random.Random) -> list[Portfolio]:
		specs = [
			("Horsten Homes", False),
			("Coastal Portfolio", False),
			("City Mixed Use", False),
		]
		portfolios: list[Portfolio] = []
		for idx, (name, archived) in enumerate(specs):
			owner = contacts[idx % len(contacts)] if contacts else None
			pf, _ = Portfolio.objects.get_or_create(
				name=name,
				defaults={
					"description": f"Demo portfolio — {name}",
					"owner_contact": owner,
					"is_archived": archived,
				},
			)
			portfolios.append(pf)
		return portfolios

	def _ensure_properties_and_units(
		self,
		portfolios: list[Portfolio],
		rng: random.Random,
	) -> list[Unit]:
		specs = [
			(portfolios[0].name if portfolios else "Horsten Homes", "Claptons Beach", [("8", 2, 1), ("12", 2, 2)]),
			(portfolios[0].name if portfolios else "Horsten Homes", "Jamaican Palms", [("8", 2, 1), ("17", 3, 2)]),
			("Coastal Portfolio", "Sea Point Heights", [("101", 2, 2), ("102", 1, 1), ("201", 3, 2)]),
			("Coastal Portfolio", "Blouberg Views", [("5", 2, 1), ("6", 2, 1)]),
			("City Mixed Use", "Sandton Central", [("A1", None, 1), ("A2", None, 1), ("B1", 1, 1)]),
		]
		portfolio_by_name = {p.name: p for p in portfolios}
		units: list[Unit] = []

		for pf_name, prop_name, unit_specs in specs:
			pf = portfolio_by_name.get(pf_name) or portfolios[0]
			prop, _ = Property.objects.get_or_create(
				portfolio=pf,
				name=prop_name,
				defaults={
					"property_type": PropertyType.RESIDENTIAL,
					"purchase_price": Decimal(str(rng.randint(850_000, 2_400_000))),
					"purchase_date": date(2020, rng.randint(1, 12), 1),
					"source": "demo",
				},
			)
			for unit_number, beds, baths in unit_specs:
				unit, _ = Unit.objects.get_or_create(
					property=prop,
					unit_number=unit_number,
					defaults={
						"bedrooms": beds,
						"bathrooms": baths,
						"purchase_date": date(2020, rng.randint(1, 12), 1),
						"purchase_price": Decimal(str(rng.randint(450_000, 1_200_000))),
						"status": UnitStatus.VACANT,
						"source": "demo",
					},
				)
				units.append(unit)

		for u in Unit.objects.all():
			if u not in units:
				units.append(u)
		return units

	def _ensure_leases(self, units: list[Unit], contacts: list[Contact], rng: random.Random) -> int:
		today = timezone.localdate()
		created = 0
		tenant_contacts = [c for c in contacts if "@" in (c.email or "") and "demo" in (c.email or "")][:10]
		if not tenant_contacts:
			tenant_contacts = contacts

		for idx, unit in enumerate(units):
			if unit.leases.filter(status=LeaseStatus.ACTIVE).exists():
				continue

			tenant = tenant_contacts[idx % len(tenant_contacts)]
			rent = Decimal(str(rng.randint(8500, 16500)))

			if idx % 7 == 0:
				continue  # leave vacant

			if idx % 5 == 0:
				end_date = None  # month-to-month
			elif idx % 4 == 0:
				end_date = today + timedelta(days=rng.randint(14, 75))
			else:
				end_date = today + timedelta(days=rng.randint(120, 540))

			start = _subtract_months(today, rng.randint(6, 36))
			Lease.objects.create(
				unit=unit,
				primary_tenant=tenant,
				status=LeaseStatus.ACTIVE,
				start_date=start,
				end_date=end_date,
				rent_amount=rent,
				deposit_amount=rent * 2,
				source="demo",
			)
			unit.status = UnitStatus.OCCUPIED
			unit.save(update_fields=["status"])
			created += 1

		# Ensure at least 2 vacant units
		vacant_targets = [u for u in units[:2]]
		for unit in vacant_targets:
			unit.leases.filter(status=LeaseStatus.ACTIVE).update(status=LeaseStatus.ENDED)
			unit.status = UnitStatus.VACANT
			unit.save(update_fields=["status"])

		return created

	def _ensure_contractors(self, contacts: list[Contact], rng: random.Random) -> int:
		specs = [
			("PlumbRight Plumbing", "plumbing", "ops@plumbright.demo"),
			("Spark Electrical", "electrical", "admin@sparkelect.demo"),
			("GreenGarden Maintenance", "landscaping", ""),
			("RoofSafe Repairs", "roofing", ""),
			("CoolAir HVAC", "hvac", ""),
		]
		created = 0
		contact_by_email = {c.email.lower(): c for c in contacts if c.email}

		for name, trade, email in specs:
			contractor, was_created = Contractor.objects.get_or_create(
				name=name,
				defaults={
					"trade": trade,
					"email": email or f"{trade}@demo.local",
					"phone": f"011 555 {rng.randint(1000, 9999)}",
					"reference": f"CTR-{trade[:3].upper()}-{rng.randint(100, 999)}",
					"is_active": True,
				},
			)
			if was_created:
				created += 1
			link = contact_by_email.get((email or "").lower())
			if link:
				contractor.contacts.add(link)
			elif contacts:
				contractor.contacts.add(contacts[rng.randint(0, len(contacts) - 1)])

		return created

	def _seed_accounting(self, units: list[Unit], *, months: int, rng: random.Random) -> tuple[int, int]:
		today = timezone.localdate()
		start_month = _subtract_months(date(today.year, today.month, 1), months - 1)
		inv_created = 0
		exp_created = 0

		for unit in units:
			base_rent = Decimal(str(rng.randint(9000, 16000)))
			base_expense = Decimal(str(rng.randint(1200, 3500)))

			for m in range(months):
				month_start = _subtract_months(date(today.year, today.month, 1), months - 1 - m)
				if month_start < start_month:
					continue

				inv_date = month_start.replace(day=min(5, 28))
				exp_date = month_start.replace(day=min(18, 28))

				drift = Decimal(str(rng.randint(-800, 800)))
				inv_amt = base_rent + drift
				exp_amt = base_expense + Decimal(str(rng.randint(0, 1200)))

				inv_desc = f"Rent invoice — {month_start.strftime('%b %Y')}"
				exp_desc = f"Operating costs — {month_start.strftime('%b %Y')}"

				if not UnitInvoice.objects.filter(unit=unit, issue_date=inv_date, description=inv_desc).exists():
					UnitInvoice.objects.create(
						unit=unit,
						issue_date=inv_date,
						amount=inv_amt,
						description=inv_desc,
					)
					inv_created += 1

				if not UnitExpense.objects.filter(unit=unit, expense_date=exp_date, description=exp_desc).exists():
					UnitExpense.objects.create(
						unit=unit,
						expense_date=exp_date,
						amount=exp_amt,
						description=exp_desc,
					)
					exp_created += 1

		return inv_created, exp_created
