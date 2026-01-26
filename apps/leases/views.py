from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin, WorkItemContextMixin
from apps.leases.forms import LeaseForm
from apps.leases.models import Lease
from apps.properties.models import Unit


class LeaseListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Lease
	template_name = "leases/lease_list.html"
	context_object_name = "leases"
	paginate_by = 25

	def get_queryset(self):
		qs = (
			Lease.objects.select_related("unit", "unit__property", "primary_tenant")
			.all()
			.order_by("-updated_at")
		)
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(
				Q(unit__unit_number__icontains=q)
				| Q(unit__property__name__icontains=q)
				| Q(primary_tenant__display_name__icontains=q)
				| Q(external_id__icontains=q)
			)
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class LeaseDetailView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Lease
	template_name = "leases/lease_detail.html"
	context_object_name = "lease"


class LeaseCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = Lease
	form_class = LeaseForm
	template_name = "leases/lease_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Lease created.")
		return resp

	def get_success_url(self):
		return reverse("leases:detail", kwargs={"pk": self.object.pk})


class LeaseCreateForUnitView(LeaseCreateView):
	def dispatch(self, request, *args, **kwargs):
		self.unit = get_object_or_404(Unit, pk=kwargs["unit_pk"])
		return super().dispatch(request, *args, **kwargs)

	def get_initial(self):
		initial = super().get_initial()
		initial["unit"] = self.unit
		return initial

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		form.fields["unit"].initial = self.unit
		form.fields["unit"].queryset = Unit.objects.filter(pk=self.unit.pk)
		return form


class LeaseUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Lease
	form_class = LeaseForm
	template_name = "leases/lease_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Lease updated.")
		return resp

	def get_success_url(self):
		return reverse("leases:detail", kwargs={"pk": self.object.pk})


class LeaseDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Lease
	success_url = reverse_lazy("leases:list")

	def delete(self, request, *args, **kwargs):
		messages.success(self.request, "Lease deleted.")
		return super().delete(request, *args, **kwargs)
