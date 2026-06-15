from __future__ import annotations

from calendar import isleap, monthrange
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db.models import DecimalField, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from apps.accounting.models import AssetCapitalInvestment
from apps.properties.models import Property, Unit

_asset_field = DecimalField(max_digits=14, decimal_places=2)
_zero = Value(Decimal("0.00"), output_field=_asset_field)


def _capital_on_property_subquery():
	return Subquery(
		AssetCapitalInvestment.objects.filter(related_property_id=OuterRef("pk"))
		.values("related_property_id")
		.annotate(total=Sum("amount"))
		.values("total")[:1],
		output_field=_asset_field,
	)


def _capital_on_property_units_subquery():
	return Subquery(
		AssetCapitalInvestment.objects.filter(unit__property_id=OuterRef("pk"))
		.values("unit__property_id")
		.annotate(total=Sum("amount"))
		.values("total")[:1],
		output_field=_asset_field,
	)


def _capital_on_portfolio_properties_subquery():
	return Subquery(
		AssetCapitalInvestment.objects.filter(related_property__portfolio_id=OuterRef("pk"))
		.values("related_property__portfolio_id")
		.annotate(total=Sum("amount"))
		.values("total")[:1],
		output_field=_asset_field,
	)


def _capital_on_portfolio_units_subquery():
	return Subquery(
		AssetCapitalInvestment.objects.filter(unit__property__portfolio_id=OuterRef("pk"))
		.values("unit__property__portfolio_id")
		.annotate(total=Sum("amount"))
		.values("total")[:1],
		output_field=_asset_field,
	)


def capital_investment_total() -> Decimal:
	return (
		AssetCapitalInvestment.objects.aggregate(total=Coalesce(Sum("amount"), _zero))["total"]
		or Decimal("0.00")
	)


def total_asset_value() -> Decimal:
	"""Sum of purchase prices and capital investments across the tenant."""
	site_total = (
		Property.objects.aggregate(total=Coalesce(Sum("purchase_price"), _zero))["total"]
		or Decimal("0.00")
	)
	unit_total = (
		Unit.objects.aggregate(total=Coalesce(Sum("purchase_price"), _zero))["total"]
		or Decimal("0.00")
	)
	return site_total + unit_total + capital_investment_total()


def unit_total_asset_value(unit: Unit) -> Decimal:
	purchase = unit.purchase_price or Decimal("0.00")
	capital = (
		unit.capital_investments.aggregate(total=Coalesce(Sum("amount"), _zero))["total"]
		or Decimal("0.00")
	)
	return purchase + capital


def annotate_properties_with_total_asset_value(qs):
	qs = qs.annotate(
		units_purchase_total=Coalesce(
			Sum("units__purchase_price"),
			_zero,
			output_field=_asset_field,
		),
		capital_on_property=Coalesce(_capital_on_property_subquery(), _zero),
		capital_on_units=Coalesce(_capital_on_property_units_subquery(), _zero),
	)
	return qs.annotate(
		total_asset_value=Coalesce(F("purchase_price"), _zero)
		+ Coalesce(F("units_purchase_total"), _zero)
		+ Coalesce(F("capital_on_property"), _zero)
		+ Coalesce(F("capital_on_units"), _zero),
	)


def annotate_portfolios_with_total_asset_value(qs):
	qs = qs.annotate(
		capital_on_properties=Coalesce(_capital_on_portfolio_properties_subquery(), _zero),
		capital_on_units=Coalesce(_capital_on_portfolio_units_subquery(), _zero),
	)
	return qs.annotate(
		total_asset_value=Coalesce(F("site_value"), _zero)
		+ Coalesce(F("unit_value"), _zero)
		+ Coalesce(F("capital_on_properties"), _zero)
		+ Coalesce(F("capital_on_units"), _zero),
	)


def _end_of_year(year: int) -> date:
	return date(year, 12, 31)


def _end_of_month(year: int, month: int) -> date:
	return date(year, month, monthrange(year, month)[1])


def _iter_months(start_year: int, start_month: int, end_year: int, end_month: int):
	year, month = start_year, start_month
	while (year, month) <= (end_year, end_month):
		yield year, month
		month += 1
		if month > 12:
			month = 1
			year += 1


def _iter_years(start_year: int, end_year: int):
	yield from range(start_year, end_year + 1)


def _annual_growth_factor(rate: Decimal, year: int, as_of: date) -> Decimal:
	if year < as_of.year:
		return Decimal("1") + rate
	if year > as_of.year:
		return Decimal("1")
	days_in_year = 366 if isleap(year) else 365
	days_elapsed = (as_of - date(year, 1, 1)).days + 1
	if days_elapsed <= 0:
		return Decimal("1")
	year_fraction = Decimal(str(days_elapsed)) / Decimal(str(days_in_year))
	return Decimal("1") + rate * year_fraction


def _monthly_growth_factor(rate: Decimal, year: int, month: int, as_of: date) -> Decimal:
	month_start = date(year, month, 1)
	if month_start > as_of:
		return Decimal("1")
	month_end = min(_end_of_month(year, month), as_of)
	days_in_month = monthrange(year, month)[1]
	days_elapsed = (month_end - month_start).days + 1
	if days_elapsed <= 0:
		return Decimal("1")
	month_fraction = Decimal(str(days_elapsed)) / Decimal(str(days_in_month))
	monthly_rate = rate / Decimal("12")
	return Decimal("1") + monthly_rate * month_fraction


def _portfolio_acquisition_events() -> list[tuple[date, Decimal, bool]]:
	events: list[tuple[date, Decimal, bool]] = []

	for prop in Property.objects.filter(
		is_archived=False,
		purchase_date__isnull=False,
		purchase_price__isnull=False,
	):
		events.append((prop.purchase_date, prop.purchase_price, False))

	for unit in Unit.objects.filter(
		property__is_archived=False,
		purchase_date__isnull=False,
		purchase_price__isnull=False,
	):
		events.append((unit.purchase_date, unit.purchase_price, False))

	for inv in AssetCapitalInvestment.objects.filter(
		Q(related_property__isnull=True) | Q(related_property__is_archived=False),
		Q(unit__isnull=True) | Q(unit__property__is_archived=False),
	):
		events.append((inv.investment_date, inv.amount, True))

	events.sort(key=lambda row: row[0])
	return events


def asset_monthly_capital_gains_map() -> dict[str, float]:
	"""Capital growth at each month-end, keyed by chart label (e.g. Jan 2026)."""
	events = _portfolio_acquisition_events()
	if not events:
		return {}

	rate = Decimal(str(getattr(settings, "ASSET_CAPITAL_GROWTH_RATE", 0.03)))
	today = date.today()
	first = events[0][0]
	invested_capital = Decimal("0")
	total_value = Decimal("0")
	event_idx = 0
	by_label: dict[str, float] = {}

	for year, month in _iter_months(first.year, first.month, today.year, today.month):
		as_of = min(_end_of_month(year, month), today)
		while event_idx < len(events) and events[event_idx][0] <= as_of:
			_, amount, _ = events[event_idx]
			invested_capital += amount
			total_value += amount
			event_idx += 1
		if invested_capital == 0:
			continue
		growth_factor = _monthly_growth_factor(rate, year, month, today)
		total_value = (total_value * growth_factor).quantize(Decimal("0.01"))
		by_label[date(year, month, 1).strftime("%b %Y")] = float(total_value - invested_capital)

	return by_label


def capital_growth_for_chart_labels(labels: list[str], *, granularity: str) -> list[float]:
	"""Align capital growth values to profit chart labels (yearly or monthly)."""
	if not labels:
		return []

	if granularity == "yearly":
		asset = asset_acquisition_chart_data()
		by_label: dict[str, float] = {}
		if asset:
			by_label = {str(row["label"]): float(row["growth"]) for row in asset["years"]}
		values: list[float] = []
		last = 0.0
		for label in labels:
			last = by_label.get(str(label), last)
			values.append(last)
		return values

	growth_map = asset_monthly_capital_gains_map()
	values = []
	last = 0.0
	for label in labels:
		if label in growth_map:
			last = growth_map[label]
		values.append(last)
	return values


def asset_acquisition_chart_data() -> dict[str, object] | None:
	"""Yearly portfolio value: invested capital compounds at the configured annual growth rate."""
	rate = Decimal(str(getattr(settings, "ASSET_CAPITAL_GROWTH_RATE", 0.03)))
	today = date.today()
	events = _portfolio_acquisition_events()
	if not events:
		return None
	first_year = events[0][0].year
	last_year = today.year
	year_rows: list[dict[str, object]] = []
	acquisitions_cum = Decimal("0")
	investments_cum = Decimal("0")
	invested_capital = Decimal("0")
	total_value = Decimal("0")
	event_idx = 0

	for year in _iter_years(first_year, last_year):
		as_of = min(_end_of_year(year), today)

		while event_idx < len(events) and events[event_idx][0] <= as_of:
			_, amount, is_investment = events[event_idx]
			invested_capital += amount
			total_value += amount
			if is_investment:
				investments_cum += amount
			else:
				acquisitions_cum += amount
			event_idx += 1

		if invested_capital == 0:
			continue

		growth_factor = _annual_growth_factor(rate, year, today)
		total_value = (total_value * growth_factor).quantize(Decimal("0.01"))
		growth = total_value - invested_capital

		year_rows.append(
			{
				"label": str(year),
				"invested_capital": float(invested_capital),
				"acquisitions": float(acquisitions_cum),
				"investments": float(investments_cum),
				"growth": float(growth),
				"total_value": float(total_value),
				"event_count": event_idx,
			}
		)

	if not year_rows:
		return None

	return {
		"growth_rate": float(rate),
		"growth_rate_pct": float(rate * 100),
		"cumulative": True,
		"years": year_rows,
	}


def capital_investments_for_property(property: Property):
	return (
		AssetCapitalInvestment.objects.filter(Q(related_property=property) | Q(unit__property=property))
		.select_related("related_property", "unit", "unit__property")
		.order_by("-investment_date", "-created_at")[:100]
	)


def capital_investments_for_unit(unit: Unit):
	return unit.capital_investments.order_by("-investment_date", "-created_at")[:100]
