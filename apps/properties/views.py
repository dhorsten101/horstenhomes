from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounting.models import UnitExpense, UnitInvoice
from apps.accounting.services import (
	pnl_charts_context,
	scoped_top_performers_context,
	units_with_pnl_for_property,
)
from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin, WorkItemContextMixin
from apps.properties.forms import PropertyForm, UnitForm
from apps.properties.models import Property, Unit, UnitStatus


class PropertyListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Property
	template_name = "properties/property_list.html"
	context_object_name = "properties"
	paginate_by = 25

	def get_queryset(self):
		qs = (
			Property.objects.select_related("portfolio", "address")
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
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(Q(name__icontains=q) | Q(external_id__icontains=q))
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class PropertyDetailView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Property
	template_name = "properties/property_detail.html"
	context_object_name = "property"

	def get_queryset(self):
		return (
			super()
			.get_queryset()
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
		)

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		prop = self.object
		ctx["units_pnl"] = units_with_pnl_for_property(prop)
		ctx.update(pnl_charts_context(self.request, Unit.objects.filter(property=prop)))
		ctx.update(scoped_top_performers_context(self.request, scope="property", property=prop))
		return ctx


class PropertyCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = Property
	form_class = PropertyForm
	template_name = "properties/property_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Property created.")
		return resp

	def get_success_url(self):
		return reverse("properties:property_detail", kwargs={"pk": self.object.pk})


class PropertyUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Property
	form_class = PropertyForm
	template_name = "properties/property_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Property updated.")
		return resp

	def get_success_url(self):
		return reverse("properties:property_detail", kwargs={"pk": self.object.pk})


class PropertyDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Property
	success_url = reverse_lazy("properties:property_list")

	def delete(self, request, *args, **kwargs):
		messages.success(self.request, "Property deleted.")
		return super().delete(request, *args, **kwargs)


class UnitListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Unit
	template_name = "properties/unit_list.html"
	context_object_name = "units"
	paginate_by = 25

	def get_queryset(self):
		qs = Unit.objects.select_related("property", "property__portfolio").all().order_by("-updated_at")
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(Q(unit_number__icontains=q) | Q(property__name__icontains=q) | Q(external_id__icontains=q))
		status = (self.request.GET.get("status") or "").strip()
		if status in UnitStatus.values:
			qs = qs.filter(status=status)
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		ctx["status"] = (self.request.GET.get("status") or "").strip()
		return ctx


class UnitDetailView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Unit
	template_name = "properties/unit_detail.html"
	context_object_name = "unit"

	def get_queryset(self):
		return Unit.objects.select_related(
			"property",
			"estate_agent",
			"estate_agent__contact",
			"managing_agent",
			"managing_agent__contact",
			"rental_agent",
			"rental_agent__contact",
		)

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		u = self.object
		ctx["unit_invoices"] = UnitInvoice.objects.filter(unit=u).order_by("-issue_date", "-created_at")[:100]
		ctx["unit_expenses"] = (
			UnitExpense.objects.filter(unit=u)
			.order_by("-expense_date", "-created_at")
			.prefetch_related("documents")[:100]
		)
		charts = pnl_charts_context(self.request, Unit.objects.filter(pk=u.pk))
		ctx.update(charts)
		ctx["net_income"] = charts["net"]
		return ctx


class UnitCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = Unit
	form_class = UnitForm
	template_name = "properties/unit_form.html"

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["request"] = self.request
		return kwargs

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Unit created.")
		return resp

	def get_success_url(self):
		return reverse("properties:unit_detail", kwargs={"pk": self.object.pk})


class UnitCreateForPropertyView(UnitCreateView):
	def dispatch(self, request, *args, **kwargs):
		self.property = get_object_or_404(Property, pk=kwargs["property_pk"])
		return super().dispatch(request, *args, **kwargs)

	def get_initial(self):
		initial = super().get_initial()
		initial["property"] = self.property
		return initial

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		form.fields["property"].initial = self.property
		form.fields["property"].queryset = Property.objects.filter(pk=self.property.pk)
		return form


class UnitUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Unit
	form_class = UnitForm
	template_name = "properties/unit_form.html"

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["request"] = self.request
		return kwargs

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Unit updated.")
		return resp

	def get_success_url(self):
		return reverse("properties:unit_detail", kwargs={"pk": self.object.pk})


class UnitDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Unit
	success_url = reverse_lazy("properties:unit_list")

	def form_valid(self, form):
		# Django 5.2+ BaseDeleteView deletes in form_valid(), not delete() — catch PROTECT there.
		try:
			response = super().form_valid(form)
		except ProtectedError:
			lease_count = self.object.leases.count()
			if lease_count:
				messages.error(
					self.request,
					"This unit cannot be deleted while it still has one or more leases "
					f"({lease_count} on file). Remove or end those leases first, then try again.",
				)
			else:
				messages.error(
					self.request,
					"This unit cannot be deleted because other records still depend on it. "
					"Remove or reassign those records first, then try again.",
				)
			return redirect("properties:unit_detail", pk=self.object.pk)
		messages.success(self.request, "Unit deleted.")
		return response
