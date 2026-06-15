from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from apps.accounting.forms import AssetCapitalInvestmentForm, UnitExpenseForm, UnitInvoiceForm
from apps.accounting.models import AssetCapitalInvestment, UnitExpense, UnitInvoice
from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin
from apps.documents.models import Document
from apps.properties.models import Property, Unit


def _capital_tab_url_for_investment(investment: AssetCapitalInvestment) -> str:
	if investment.unit_id:
		return f"{reverse('properties:unit_detail', kwargs={'pk': investment.unit_id})}?tab=capital"
	return f"{reverse('properties:property_detail', kwargs={'pk': investment.related_property_id})}?tab=capital"


class UnitInvoiceCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = UnitInvoice
	form_class = UnitInvoiceForm
	template_name = "accounting/unit_invoice_form.html"

	def dispatch(self, request, *args, **kwargs):
		self.unit = get_object_or_404(Unit, pk=kwargs["unit_pk"])
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["unit"] = self.unit
		ctx["form_title"] = f"New invoice — {self.unit.unit_number}"
		return ctx

	def form_valid(self, form):
		form.instance.unit = self.unit
		resp = super().form_valid(form)
		messages.success(self.request, "Invoice added.")
		return resp

	def get_success_url(self) -> str:
		return f"{reverse('properties:unit_detail', kwargs={'pk': self.unit.pk})}?tab=invoices"


class UnitExpenseCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = UnitExpense
	form_class = UnitExpenseForm
	template_name = "accounting/unit_expense_form.html"

	def dispatch(self, request, *args, **kwargs):
		self.unit = get_object_or_404(Unit, pk=kwargs["unit_pk"])
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["unit"] = self.unit
		ctx["form_title"] = f"New expense — {self.unit.unit_number}"
		return ctx

	def form_valid(self, form):
		form.instance.unit = self.unit
		attachment = form.cleaned_data.get("attachment")
		resp = super().form_valid(form)
		if attachment:
			expense = self.object
			ct = ContentType.objects.get_for_model(expense, for_concrete_model=False)
			title = (form.cleaned_data.get("description") or "").strip()[:200] or "Expense attachment"
			Document.objects.create(
				content_type=ct,
				object_id=expense.pk,
				file=attachment,
				title=title,
				uploaded_by=self.request.user,
			)
		messages.success(self.request, "Expense added.")
		return resp

	def get_success_url(self) -> str:
		return f"{reverse('properties:unit_detail', kwargs={'pk': self.unit.pk})}?tab=expenses"


class UnitCapitalInvestmentCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = AssetCapitalInvestment
	form_class = AssetCapitalInvestmentForm
	template_name = "accounting/unit_capital_investment_form.html"

	def dispatch(self, request, *args, **kwargs):
		self.unit = get_object_or_404(Unit, pk=kwargs["unit_pk"])
		return super().dispatch(request, *args, **kwargs)

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		form.instance.unit = self.unit
		return form

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["unit"] = self.unit
		ctx["form_title"] = f"Capital investment — {self.unit.unit_number}"
		return ctx

	def form_valid(self, form):
		form.instance.unit = self.unit
		resp = super().form_valid(form)
		messages.success(self.request, "Capital investment recorded.")
		return resp

	def get_success_url(self) -> str:
		return f"{reverse('properties:unit_detail', kwargs={'pk': self.unit.pk})}?tab=capital"


class PropertyCapitalInvestmentCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = AssetCapitalInvestment
	form_class = AssetCapitalInvestmentForm
	template_name = "accounting/property_capital_investment_form.html"

	def dispatch(self, request, *args, **kwargs):
		self.property = get_object_or_404(Property, pk=kwargs["property_pk"])
		return super().dispatch(request, *args, **kwargs)

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		form.instance.related_property = self.property
		return form

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["property"] = self.property
		ctx["form_title"] = f"Capital investment — {self.property.name}"
		return ctx

	def form_valid(self, form):
		form.instance.related_property = self.property
		resp = super().form_valid(form)
		messages.success(self.request, "Capital investment recorded.")
		return resp

	def get_success_url(self) -> str:
		return f"{reverse('properties:property_detail', kwargs={'pk': self.property.pk})}?tab=capital"


class CapitalInvestmentUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = AssetCapitalInvestment
	form_class = AssetCapitalInvestmentForm
	template_name = "accounting/capital_investment_form.html"

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		inv = self.object
		ctx["form_title"] = f"Edit capital investment — {inv.asset_label}"
		ctx["back_url"] = _capital_tab_url_for_investment(inv)
		ctx["back_label"] = "Capital investments"
		ctx["submit_text"] = "Save changes"
		return ctx

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Capital investment updated.")
		return resp

	def get_success_url(self) -> str:
		return _capital_tab_url_for_investment(self.object)


class CapitalInvestmentDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = AssetCapitalInvestment

	def delete(self, request, *args, **kwargs):
		self.object = self.get_object()
		self.success_url = _capital_tab_url_for_investment(self.object)
		messages.success(request, "Capital investment deleted.")
		return super().delete(request, *args, **kwargs)
