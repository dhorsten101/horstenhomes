from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.contractors.forms import ContractorForm
from apps.contractors.models import Contractor
from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin


class ContractorListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Contractor
	template_name = "contractors/contractor_list.html"
	context_object_name = "contractors"
	paginate_by = 25

	def get_queryset(self):
		qs = (
			Contractor.objects.select_related("address")
			.annotate(contact_count=Count("contacts"))
			.all()
			.order_by("name")
		)
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(
				Q(name__icontains=q)
				| Q(trade__icontains=q)
				| Q(email__icontains=q)
				| Q(phone__icontains=q)
				| Q(reference__icontains=q)
				| Q(contacts__display_name__icontains=q)
			).distinct()
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class ContractorDetailView(TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Contractor
	template_name = "contractors/contractor_detail.html"
	context_object_name = "contractor"

	def get_queryset(self):
		return Contractor.objects.select_related("address").prefetch_related("contacts")


class ContractorCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = Contractor
	form_class = ContractorForm
	template_name = "contractors/contractor_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Contractor created.")
		return resp

	def get_success_url(self):
		return reverse("contractors:detail", kwargs={"pk": self.object.pk})


class ContractorUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Contractor
	form_class = ContractorForm
	template_name = "contractors/contractor_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Contractor updated.")
		return resp

	def get_success_url(self):
		return reverse("contractors:detail", kwargs={"pk": self.object.pk})


class ContractorDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Contractor
	success_url = reverse_lazy("contractors:list")

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Contractor deleted.")
		return resp
