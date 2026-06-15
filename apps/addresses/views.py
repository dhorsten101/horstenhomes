from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.addresses.forms import AddressForm
from apps.addresses.models import Address
from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin, WorkItemContextMixin


class AddressListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Address
	template_name = "addresses/address_list.html"
	context_object_name = "addresses"
	paginate_by = 25

	def get_queryset(self):
		qs = Address.objects.all().order_by("-updated_at")
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(
				Q(label__icontains=q)
				| Q(line1__icontains=q)
				| Q(line2__icontains=q)
				| Q(city__icontains=q)
				| Q(region__icontains=q)
				| Q(postal_code__icontains=q)
				| Q(country__icontains=q)
			)
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class AddressDetailView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Address
	template_name = "addresses/address_detail.html"
	context_object_name = "address"


class AddressCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = Address
	form_class = AddressForm
	template_name = "addresses/address_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Address created.")
		return resp

	def get_success_url(self):
		return reverse("addresses:detail", kwargs={"pk": self.object.pk})


class AddressUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Address
	form_class = AddressForm
	template_name = "addresses/address_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Address updated.")
		return resp

	def get_success_url(self):
		return reverse("addresses:detail", kwargs={"pk": self.object.pk})


class AddressDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Address
	success_url = reverse_lazy("addresses:list")

	def delete(self, request, *args, **kwargs):
		messages.success(self.request, "Address deleted.")
		return super().delete(request, *args, **kwargs)


class AddressQuickCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, View):
	"""HTMX modal: create an address and select it on the parent form."""

	template_name = "addresses/includes/address_quick_create_form.html"

	def get(self, request):
		return render(
			request,
			self.template_name,
			{
				"form": AddressForm(),
				"field_id": (request.GET.get("field_id") or "").strip(),
			},
		)

	def post(self, request):
		field_id = (request.POST.get("field_id") or "").strip()
		form = AddressForm(request.POST)
		if not form.is_valid():
			return render(
				request,
				self.template_name,
				{"form": form, "field_id": field_id},
				status=422,
				headers={"HX-Retarget": "#addressQuickCreateModalBody", "HX-Reswap": "innerHTML"},
			)
		address = form.save()
		response = HttpResponse(status=204)
		response["HX-Trigger"] = json.dumps(
			{
				"addressCreated": {
					"id": address.pk,
					"label": str(address),
					"fieldId": field_id,
				}
			}
		)
		return response
