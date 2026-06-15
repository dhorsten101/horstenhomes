from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView

from apps.accounting.forms import UnitExpenseForm, UnitInvoiceForm
from apps.accounting.models import UnitExpense, UnitInvoice
from apps.core.mixins import TenantSchemaRequiredMixin
from apps.documents.models import Document
from apps.properties.models import Unit


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
		return reverse("properties:unit_detail", kwargs={"pk": self.unit.pk})


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
		return reverse("properties:unit_detail", kwargs={"pk": self.unit.pk})
