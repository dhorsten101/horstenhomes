from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin
from apps.portfolio.forms import PortfolioForm
from apps.portfolio.models import Portfolio


class PortfolioListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Portfolio
	template_name = "portfolio/portfolio_list.html"
	context_object_name = "portfolios"
	paginate_by = 25

	def get_queryset(self):
		qs = (
			Portfolio.objects.select_related("owner_contact")
			.annotate(property_count=Count("properties"))
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


class PortfolioDetailView(TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Portfolio
	template_name = "portfolio/portfolio_detail.html"
	context_object_name = "portfolio"


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
