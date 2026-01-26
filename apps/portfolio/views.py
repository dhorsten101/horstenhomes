from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin, WorkItemContextMixin
from apps.portfolio.forms import PortfolioForm
from apps.portfolio.models import Portfolio
from apps.properties.models import Property, Unit


class PortfolioListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Portfolio
	template_name = "portfolio/portfolio_list.html"
	context_object_name = "portfolios"
	paginate_by = 25

	def get_queryset(self):
		site_value_subquery = (
			Property.objects.filter(portfolio_id=OuterRef("pk"))
			.values("portfolio_id")
			.annotate(
				total=Coalesce(
					Sum("purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)
			.values("total")[:1]
		)

		unit_value_subquery = (
			Unit.objects.filter(property__portfolio_id=OuterRef("pk"))
			.values("property__portfolio_id")
			.annotate(
				total=Coalesce(
					Sum("purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)
			.values("total")[:1]
		)

		qs = (
			Portfolio.objects.select_related("owner_contact")
			.annotate(property_count=Count("properties"))
			.annotate(site_value=Subquery(site_value_subquery))
			.annotate(unit_value=Subquery(unit_value_subquery))
			.annotate(
				total_asset_value=Coalesce("site_value", Value(Decimal("0.00"))) + Coalesce("unit_value", Value(Decimal("0.00")))
			)
			.order_by("-updated_at")
		)
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class PortfolioDetailView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Portfolio
	template_name = "portfolio/portfolio_detail.html"
	context_object_name = "portfolio"

	def get_queryset(self):
		site_value_subquery = (
			Property.objects.filter(portfolio_id=OuterRef("pk"))
			.values("portfolio_id")
			.annotate(
				total=Coalesce(
					Sum("purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)
			.values("total")[:1]
		)

		unit_value_subquery = (
			Unit.objects.filter(property__portfolio_id=OuterRef("pk"))
			.values("property__portfolio_id")
			.annotate(
				total=Coalesce(
					Sum("purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)
			.values("total")[:1]
		)

		return (
			super()
			.get_queryset()
			.select_related("owner_contact")
			.annotate(site_value=Subquery(site_value_subquery))
			.annotate(unit_value=Subquery(unit_value_subquery))
			.annotate(
				total_asset_value=Coalesce("site_value", Value(Decimal("0.00"))) + Coalesce("unit_value", Value(Decimal("0.00")))
			)
		)

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		p = self.object

		# Properties in this portfolio (include rollups)
		ctx["properties"] = (
			Property.objects.filter(portfolio=p)
			.select_related("portfolio", "address")
			.annotate(
				units_purchase_total=Coalesce(
					Sum("units__purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)
			.annotate(
				total_asset_value=Coalesce(
					F("purchase_price"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
				+ Coalesce(
					F("units_purchase_total"),
					Value(Decimal("0.00")),
					output_field=DecimalField(max_digits=14, decimal_places=2),
				)
			)
			.order_by("-updated_at")
		)

		return ctx


class PortfolioCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = Portfolio
	form_class = PortfolioForm
	template_name = "portfolio/portfolio_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Portfolio created.")
		return resp

	def get_success_url(self):
		return reverse("portfolio:detail", kwargs={"pk": self.object.pk})


class PortfolioUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Portfolio
	form_class = PortfolioForm
	template_name = "portfolio/portfolio_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Portfolio updated.")
		return resp

	def get_success_url(self):
		return reverse("portfolio:detail", kwargs={"pk": self.object.pk})


class PortfolioDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Portfolio
	success_url = reverse_lazy("portfolio:list")

	def delete(self, request, *args, **kwargs):
		messages.success(self.request, "Portfolio deleted.")
		return super().delete(request, *args, **kwargs)
