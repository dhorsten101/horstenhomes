from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from apps.accounting.services import (
	pnl_charts_context,
	properties_with_pnl_for_portfolio,
	scoped_top_performers_context,
	units_with_pnl_for_property,
)
from apps.core.mixins import TenantSchemaRequiredMixin, WorkItemContextMixin
from apps.portfolio.models import Portfolio
from apps.properties.models import Property, Unit


class UnitPnlDashboardView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Unit
	template_name = "dashboards/unit_pnl.html"
	context_object_name = "unit"

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx.update(pnl_charts_context(self.request, Unit.objects.filter(pk=self.object.pk)))
		return ctx


class PropertyPnlDashboardView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Property
	template_name = "dashboards/property_pnl.html"
	context_object_name = "property"

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		prop = self.object
		ctx["units_pnl"] = units_with_pnl_for_property(prop)
		ctx.update(pnl_charts_context(self.request, Unit.objects.filter(property=prop)))
		ctx.update(scoped_top_performers_context(self.request, scope="property", property=prop))
		return ctx


class PortfolioPnlDashboardView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Portfolio
	template_name = "dashboards/portfolio_pnl.html"
	context_object_name = "portfolio"

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		pf = self.object
		ctx["properties_pnl"] = properties_with_pnl_for_portfolio(pf)
		ctx.update(pnl_charts_context(self.request, Unit.objects.filter(property__portfolio=pf)))
		ctx.update(scoped_top_performers_context(self.request, scope="portfolio", portfolio=pf))
		return ctx
