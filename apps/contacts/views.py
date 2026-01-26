from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.contacts.forms import ContactForm
from apps.contacts.models import Contact
from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin, WorkItemContextMixin


class ContactListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Contact
	template_name = "contacts/contact_list.html"
	context_object_name = "contacts"
	paginate_by = 25

	def get_queryset(self):
		qs = Contact.objects.select_related("address").all().order_by("-updated_at")
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(
				Q(display_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q) | Q(external_id__icontains=q)
			)
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class ContactDetailView(WorkItemContextMixin, TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Contact
	template_name = "contacts/contact_detail.html"
	context_object_name = "contact"


class ContactCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = Contact
	form_class = ContactForm
	template_name = "contacts/contact_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Contact created.")
		return resp

	def get_success_url(self):
		return reverse("contacts:detail", kwargs={"pk": self.object.pk})


class ContactUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Contact
	form_class = ContactForm
	template_name = "contacts/contact_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Contact updated.")
		return resp

	def get_success_url(self):
		return reverse("contacts:detail", kwargs={"pk": self.object.pk})


class ContactDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Contact
	success_url = reverse_lazy("contacts:list")

	def delete(self, request, *args, **kwargs):
		messages.success(self.request, "Contact deleted.")
		return super().delete(request, *args, **kwargs)
