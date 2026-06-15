from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, ExtractYear, TruncMonth
from django.db.models.query import QuerySet

from apps.accounting.models import UnitExpense, UnitInvoice
from apps.portfolio.models import Portfolio
from apps.properties.models import Property, Unit


def pnl_totals(
	*,
	unit_pk: int | None = None,
	property_pk: int | None = None,
	portfolio_pk: int | None = None,
	year: int | None = None,
) -> dict[str, Decimal]:
	"""Sum invoices and expenses for one unit, one property, or one portfolio (via its units)."""
	inv_q = UnitInvoice.objects.all()
	exp_q = UnitExpense.objects.all()
	if unit_pk is not None:
		inv_q = inv_q.filter(unit_id=unit_pk)
		exp_q = exp_q.filter(unit_id=unit_pk)
	elif property_pk is not None:
		inv_q = inv_q.filter(unit__property_id=property_pk)
		exp_q = exp_q.filter(unit__property_id=property_pk)
	elif portfolio_pk is not None:
		inv_q = inv_q.filter(unit__property__portfolio_id=portfolio_pk)
		exp_q = exp_q.filter(unit__property__portfolio_id=portfolio_pk)
	else:
		raise ValueError("Specify exactly one of unit_pk, property_pk, portfolio_pk")

	if year is not None:
		inv_q = inv_q.filter(issue_date__year=year)
		exp_q = exp_q.filter(expense_date__year=year)

	inv = inv_q.aggregate(s=Sum("amount"))["s"]
	exp = exp_q.aggregate(s=Sum("amount"))["s"]
	invoices_total = inv or Decimal("0.00")
	expenses_total = exp or Decimal("0.00")
	return {
		"invoices_total": invoices_total,
		"expenses_total": expenses_total,
		"net": invoices_total - expenses_total,
	}


def pnl_totals_for_units(unit_qs: QuerySet[Unit], *, year: int | None = None) -> dict[str, Decimal]:
	"""Sum invoices and expenses for all units in the queryset."""
	ids = list(unit_qs.values_list("pk", flat=True))
	if not ids:
		return {
			"invoices_total": Decimal("0.00"),
			"expenses_total": Decimal("0.00"),
			"net": Decimal("0.00"),
		}
	inv_q = UnitInvoice.objects.filter(unit_id__in=ids)
	exp_q = UnitExpense.objects.filter(unit_id__in=ids)
	if year is not None:
		inv_q = inv_q.filter(issue_date__year=year)
		exp_q = exp_q.filter(expense_date__year=year)
	inv = inv_q.aggregate(s=Sum("amount"))["s"]
	exp = exp_q.aggregate(s=Sum("amount"))["s"]
	invoices_total = inv or Decimal("0.00")
	expenses_total = exp or Decimal("0.00")
	return {
		"invoices_total": invoices_total,
		"expenses_total": expenses_total,
		"net": invoices_total - expenses_total,
	}


def accounting_years_for_units(unit_qs: QuerySet[Unit]) -> list[int]:
	"""Distinct calendar years with invoice or expense activity."""
	ids = list(unit_qs.values_list("pk", flat=True))
	if not ids:
		return []
	inv_years = UnitInvoice.objects.filter(unit_id__in=ids).dates("issue_date", "year")
	exp_years = UnitExpense.objects.filter(unit_id__in=ids).dates("expense_date", "year")
	return sorted({d.year for d in inv_years} | {d.year for d in exp_years}, reverse=True)


def pnl_default_year() -> int:
	return date.today().year


def pnl_year_from_request(request) -> int | None:
	"""Parse ?year= from the request; defaults to the current calendar year. Use ?year=all for all years."""
	raw = (request.GET.get("year") or "").strip()
	if raw.lower() == "all":
		return None
	if not raw:
		return pnl_default_year()
	try:
		year = int(raw)
	except ValueError:
		return pnl_default_year()
	if year < 1900 or year > 2100:
		return pnl_default_year()
	return year


def pnl_charts_context(request, unit_qs: QuerySet[Unit]) -> dict:
	"""Summary totals, period/cumulative chart data, and year filter state."""
	selected_year = pnl_year_from_request(request)
	t = pnl_totals_for_units(unit_qs, year=selected_year)
	if selected_year is not None:
		period_chart = accounting_monthly_bar_series_for_units(unit_qs, year=selected_year)
		cumulative_chart = accounting_cumulative_monthly_series_for_units(unit_qs, year=selected_year)
		granularity = "monthly"
	else:
		period_chart = accounting_yearly_bar_series_for_units(unit_qs)
		cumulative_chart = accounting_cumulative_yearly_series_for_units(unit_qs)
		granularity = "yearly"
	available_years = accounting_years_for_units(unit_qs)
	current_year = pnl_default_year()
	if current_year not in available_years:
		available_years = sorted(set(available_years) | {current_year}, reverse=True)
	return {
		"invoices_total": t["invoices_total"],
		"expenses_total": t["expenses_total"],
		"net": t["net"],
		"monthly_pnl_chart": period_chart,
		"cumulative_pnl_chart": cumulative_chart,
		"pnl_chart_granularity": granularity,
		"selected_year": selected_year,
		"available_years": available_years,
	}


def unit_accounting_chart_series(unit: Unit) -> dict[str, list] | None:
	"""Daily cumulative invoice and expense totals for one unit (Chart.js payload)."""
	return accounting_chart_series_for_units(Unit.objects.filter(pk=unit.pk))


def accounting_chart_series_for_units(unit_qs: QuerySet[Unit]) -> dict[str, list] | None:
	"""Merge all invoices/expenses for the given units; cumulative series by calendar day."""
	ids = list(unit_qs.values_list("pk", flat=True))
	if not ids:
		return None

	inv_by: defaultdict[date, Decimal] = defaultdict(lambda: Decimal("0"))
	for d, amt in UnitInvoice.objects.filter(unit_id__in=ids).values_list("issue_date", "amount"):
		inv_by[d] += amt
	exp_by: defaultdict[date, Decimal] = defaultdict(lambda: Decimal("0"))
	for d, amt in UnitExpense.objects.filter(unit_id__in=ids).values_list("expense_date", "amount"):
		exp_by[d] += amt

	all_dates = set(inv_by) | set(exp_by)
	if not all_dates:
		return None

	d_min = min(all_dates)
	d_max = max(all_dates)
	labels: list[str] = []
	inv_series: list[float] = []
	exp_series: list[float] = []
	ri = Decimal("0")
	re = Decimal("0")
	cur = d_min
	while cur <= d_max:
		ri += inv_by[cur]
		re += exp_by[cur]
		labels.append(cur.isoformat())
		inv_series.append(float(ri))
		exp_series.append(float(re))
		cur += timedelta(days=1)
	return {
		"labels": labels,
		"invoices": inv_series,
		"expenses": exp_series,
		"profit": [float(i - e) for i, e in zip(inv_series, exp_series, strict=False)],
	}


def accounting_monthly_bar_series_for_units(
	unit_qs: QuerySet[Unit],
	*,
	year: int | None = None,
	max_months: int | None = 24,
) -> dict[str, list] | None:
	"""Monthly invoice and expense totals for a Chart.js bar chart."""
	ids = list(unit_qs.values_list("pk", flat=True))
	if not ids:
		return None

	def _monthly_totals(model, date_field: str) -> dict[date, Decimal]:
		by_month: dict[date, Decimal] = {}
		qs = model.objects.filter(unit_id__in=ids)
		if year is not None:
			qs = qs.filter(**{f"{date_field}__year": year})
		qs = (
			qs.annotate(month=TruncMonth(date_field))
			.values("month")
			.annotate(total=Sum("amount"))
			.order_by("month")
		)
		for row in qs:
			month_val = row["month"]
			key = month_val.date() if hasattr(month_val, "date") else month_val
			by_month[key] = row["total"] or Decimal("0.00")
		return by_month

	inv_by = _monthly_totals(UnitInvoice, "issue_date")
	exp_by = _monthly_totals(UnitExpense, "expense_date")
	all_months = sorted(set(inv_by) | set(exp_by))
	if not all_months:
		return None
	if year is None and max_months is not None and len(all_months) > max_months:
		all_months = all_months[-max_months:]

	labels: list[str] = []
	invoices: list[float] = []
	expenses: list[float] = []
	net: list[float] = []
	for month in all_months:
		inv = inv_by.get(month, Decimal("0.00"))
		exp = exp_by.get(month, Decimal("0.00"))
		labels.append(month.strftime("%b %Y"))
		invoices.append(float(inv))
		expenses.append(float(exp))
		net.append(float(inv - exp))
	return {"labels": labels, "invoices": invoices, "expenses": expenses, "net": net}


def accounting_yearly_bar_series_for_units(unit_qs: QuerySet[Unit]) -> dict[str, list] | None:
	"""Yearly invoice and expense totals for a Chart.js bar chart."""
	ids = list(unit_qs.values_list("pk", flat=True))
	if not ids:
		return None

	def _yearly_totals(model, date_field: str) -> dict[int, Decimal]:
		by_year: dict[int, Decimal] = {}
		qs = (
			model.objects.filter(unit_id__in=ids)
			.annotate(year=ExtractYear(date_field))
			.values("year")
			.annotate(total=Sum("amount"))
			.order_by("year")
		)
		for row in qs:
			by_year[row["year"]] = row["total"] or Decimal("0.00")
		return by_year

	inv_by = _yearly_totals(UnitInvoice, "issue_date")
	exp_by = _yearly_totals(UnitExpense, "expense_date")
	all_years = sorted(set(inv_by) | set(exp_by))
	if not all_years:
		return None

	labels: list[str] = []
	invoices: list[float] = []
	expenses: list[float] = []
	net: list[float] = []
	for year in all_years:
		inv = inv_by.get(year, Decimal("0.00"))
		exp = exp_by.get(year, Decimal("0.00"))
		labels.append(str(year))
		invoices.append(float(inv))
		expenses.append(float(exp))
		net.append(float(inv - exp))
	return {"labels": labels, "invoices": invoices, "expenses": expenses, "net": net}


def accounting_cumulative_monthly_series_for_units(
	unit_qs: QuerySet[Unit],
	*,
	year: int | None = None,
	max_months: int | None = 24,
) -> dict[str, list] | None:
	"""Running totals of money in, money out, and profit by month."""
	monthly = accounting_monthly_bar_series_for_units(
		unit_qs,
		year=year,
		max_months=max_months,
	)
	if not monthly:
		return None
	inv_run = 0.0
	exp_run = 0.0
	inv_cum: list[float] = []
	exp_cum: list[float] = []
	profit_cum: list[float] = []
	for inv, exp in zip(monthly["invoices"], monthly["expenses"], strict=True):
		inv_run += inv
		exp_run += exp
		inv_cum.append(inv_run)
		exp_cum.append(exp_run)
		profit_cum.append(inv_run - exp_run)
	return {
		"labels": monthly["labels"],
		"invoices": inv_cum,
		"expenses": exp_cum,
		"profit": profit_cum,
	}


def accounting_cumulative_yearly_series_for_units(unit_qs: QuerySet[Unit]) -> dict[str, list] | None:
	"""Running totals of money in, money out, and profit by year."""
	yearly = accounting_yearly_bar_series_for_units(unit_qs)
	if not yearly:
		return None
	inv_run = 0.0
	exp_run = 0.0
	inv_cum: list[float] = []
	exp_cum: list[float] = []
	profit_cum: list[float] = []
	for inv, exp in zip(yearly["invoices"], yearly["expenses"], strict=True):
		inv_run += inv
		exp_run += exp
		inv_cum.append(inv_run)
		exp_cum.append(exp_run)
		profit_cum.append(inv_run - exp_run)
	return {
		"labels": yearly["labels"],
		"invoices": inv_cum,
		"expenses": exp_cum,
		"profit": profit_cum,
	}


_dec16 = DecimalField(max_digits=16, decimal_places=2)
_zero = Value(Decimal("0.00"), output_field=_dec16)


def _unit_invoice_subquery(year: int | None = None) -> Subquery:
	qs = UnitInvoice.objects.filter(unit_id=OuterRef("pk"))
	if year is not None:
		qs = qs.filter(issue_date__year=year)
	return Subquery(
		qs.values("unit_id").annotate(total=Sum("amount")).values("total")[:1],
		output_field=_dec16,
	)


def _unit_expense_subquery(year: int | None = None) -> Subquery:
	qs = UnitExpense.objects.filter(unit_id=OuterRef("pk"))
	if year is not None:
		qs = qs.filter(expense_date__year=year)
	return Subquery(
		qs.values("unit_id").annotate(total=Sum("amount")).values("total")[:1],
		output_field=_dec16,
	)


def _property_invoice_subquery(year: int | None = None) -> Subquery:
	qs = UnitInvoice.objects.filter(unit__property_id=OuterRef("pk"))
	if year is not None:
		qs = qs.filter(issue_date__year=year)
	return Subquery(
		qs.values("unit__property_id").annotate(total=Sum("amount")).values("total")[:1],
		output_field=_dec16,
	)


def _property_expense_subquery(year: int | None = None) -> Subquery:
	qs = UnitExpense.objects.filter(unit__property_id=OuterRef("pk"))
	if year is not None:
		qs = qs.filter(expense_date__year=year)
	return Subquery(
		qs.values("unit__property_id").annotate(total=Sum("amount")).values("total")[:1],
		output_field=_dec16,
	)


def _portfolio_invoice_subquery(year: int | None = None) -> Subquery:
	qs = UnitInvoice.objects.filter(unit__property__portfolio_id=OuterRef("pk"))
	if year is not None:
		qs = qs.filter(issue_date__year=year)
	return Subquery(
		qs.values("unit__property__portfolio_id").annotate(total=Sum("amount")).values("total")[:1],
		output_field=_dec16,
	)


def _portfolio_expense_subquery(year: int | None = None) -> Subquery:
	qs = UnitExpense.objects.filter(unit__property__portfolio_id=OuterRef("pk"))
	if year is not None:
		qs = qs.filter(expense_date__year=year)
	return Subquery(
		qs.values("unit__property__portfolio_id").annotate(total=Sum("amount")).values("total")[:1],
		output_field=_dec16,
	)


def annotate_unit_pnl(qs: QuerySet[Unit], *, year: int | None = None) -> QuerySet[Unit]:
	return qs.annotate(
		pnl_invoices=Coalesce(_unit_invoice_subquery(year), _zero),
		pnl_expenses=Coalesce(_unit_expense_subquery(year), _zero),
	).annotate(pnl_net=ExpressionWrapper(F("pnl_invoices") - F("pnl_expenses"), output_field=_dec16))


def annotate_property_pnl(qs: QuerySet[Property], *, year: int | None = None) -> QuerySet[Property]:
	return qs.annotate(
		pnl_invoices=Coalesce(_property_invoice_subquery(year), _zero),
		pnl_expenses=Coalesce(_property_expense_subquery(year), _zero),
	).annotate(pnl_net=ExpressionWrapper(F("pnl_invoices") - F("pnl_expenses"), output_field=_dec16))


def annotate_portfolio_pnl(qs: QuerySet[Portfolio], *, year: int | None = None) -> QuerySet[Portfolio]:
	return qs.annotate(
		pnl_invoices=Coalesce(_portfolio_invoice_subquery(year), _zero),
		pnl_expenses=Coalesce(_portfolio_expense_subquery(year), _zero),
	).annotate(pnl_net=ExpressionWrapper(F("pnl_invoices") - F("pnl_expenses"), output_field=_dec16))


def _performer_with_activity(qs: QuerySet, *, lowest: bool = False):
	"""Best or worst net P&L among rows with invoice or expense activity in the period."""
	order = ("pnl_net", "pk") if lowest else ("-pnl_net", "pk")
	return (
		qs.filter(Q(pnl_invoices__gt=0) | Q(pnl_expenses__gt=0))
		.order_by(*order)
		.first()
	)


def top_performers_for_year(*, year: int | None = None) -> dict[str, Unit | Property | Portfolio | None]:
	"""Best and worst unit, property, and portfolio by net P&L for the given year (None = all years)."""
	unit_qs = annotate_unit_pnl(Unit.objects.select_related("property"), year=year)
	property_qs = annotate_property_pnl(Property.objects.select_related("portfolio"), year=year)
	portfolio_qs = annotate_portfolio_pnl(Portfolio.objects.all(), year=year)
	return {
		"top_performer_scope": "global",
		"top_unit": _performer_with_activity(unit_qs),
		"top_property": _performer_with_activity(property_qs),
		"top_portfolio": _performer_with_activity(portfolio_qs),
		"bottom_unit": _performer_with_activity(unit_qs, lowest=True),
		"bottom_property": _performer_with_activity(property_qs, lowest=True),
		"bottom_portfolio": _performer_with_activity(portfolio_qs, lowest=True),
	}


def top_performers_for_portfolio(portfolio: Portfolio, *, year: int | None = None) -> dict[str, Property | Unit | None]:
	"""Best and worst property and unit within one portfolio."""
	property_qs = annotate_property_pnl(Property.objects.filter(portfolio=portfolio), year=year)
	unit_qs = annotate_unit_pnl(
		Unit.objects.filter(property__portfolio=portfolio).select_related("property"),
		year=year,
	)
	return {
		"top_performer_scope": "portfolio",
		"top_property": _performer_with_activity(property_qs),
		"top_unit": _performer_with_activity(unit_qs),
		"bottom_property": _performer_with_activity(property_qs, lowest=True),
		"bottom_unit": _performer_with_activity(unit_qs, lowest=True),
	}


def top_performers_for_property(property: Property, *, year: int | None = None) -> dict[str, Unit | None]:
	"""Best and worst unit within one property."""
	unit_qs = annotate_unit_pnl(Unit.objects.filter(property=property).select_related("property"), year=year)
	return {
		"top_performer_scope": "property",
		"top_unit": _performer_with_activity(unit_qs),
		"bottom_unit": _performer_with_activity(unit_qs, lowest=True),
	}


def scoped_top_performers_context(
	request,
	*,
	scope: str,
	portfolio: Portfolio | None = None,
	property: Property | None = None,
) -> dict:
	"""Top and bottom performer cards for dashboard (global), portfolio, or property detail views."""
	year = pnl_year_from_request(request)
	if scope == "global":
		return top_performers_for_year(year=year)
	if scope == "portfolio" and portfolio is not None:
		return top_performers_for_portfolio(portfolio, year=year)
	if scope == "property" and property is not None:
		return top_performers_for_property(property, year=year)
	return {}


def units_with_pnl_for_property(property: Property) -> QuerySet[Unit]:
	return annotate_unit_pnl(Unit.objects.filter(property=property)).order_by("unit_number")


def properties_with_pnl_for_portfolio(portfolio: Portfolio) -> QuerySet[Property]:
	return annotate_property_pnl(Property.objects.filter(portfolio=portfolio)).order_by("name")
