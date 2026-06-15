from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin
from apps.rental_agents.forms import RentalAgentForm
from apps.rental_agents.models import RentalAgent


def _agent_queryset():
	return RentalAgent.objects.select_related("contact", "contact__address")


class RentalAgentListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = RentalAgent
	template_name = "rental_agents/rental_agent_list.html"
	context_object_name = "agents"
	paginate_by = 25

	def get_queryset(self):
		qs = _agent_queryset().all()
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(
				Q(name__icontains=q)
				| Q(contact__display_name__icontains=q)
				| Q(contact__email__icontains=q)
				| Q(contact__phone__icontains=q)
				| Q(reference__icontains=q)
			)
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class RentalAgentDetailView(TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = RentalAgent
	template_name = "rental_agents/rental_agent_detail.html"
	context_object_name = "agent"

	def get_queryset(self):
		return _agent_queryset()


class RentalAgentCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = RentalAgent
	form_class = RentalAgentForm
	template_name = "rental_agents/rental_agent_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Rental agent created.")
		return resp

	def get_success_url(self):
		return reverse("rental_agents:detail", kwargs={"pk": self.object.pk})


class RentalAgentUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = RentalAgent
	form_class = RentalAgentForm
	template_name = "rental_agents/rental_agent_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Rental agent updated.")
		return resp

	def get_success_url(self):
		return reverse("rental_agents:detail", kwargs={"pk": self.object.pk})


class RentalAgentDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = RentalAgent
	success_url = reverse_lazy("rental_agents:list")

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Rental agent deleted.")
		return resp
