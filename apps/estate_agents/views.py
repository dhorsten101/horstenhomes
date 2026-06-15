from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin
from apps.estate_agents.forms import EstateAgentForm
from apps.estate_agents.models import EstateAgent


def _agent_queryset():
	return EstateAgent.objects.select_related("contact", "contact__address")


class EstateAgentListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = EstateAgent
	template_name = "estate_agents/estate_agent_list.html"
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


class EstateAgentDetailView(TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = EstateAgent
	template_name = "estate_agents/estate_agent_detail.html"
	context_object_name = "agent"

	def get_queryset(self):
		return _agent_queryset()


class EstateAgentCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = EstateAgent
	form_class = EstateAgentForm
	template_name = "estate_agents/estate_agent_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Estate agent created.")
		return resp

	def get_success_url(self):
		return reverse("estate_agents:detail", kwargs={"pk": self.object.pk})


class EstateAgentUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = EstateAgent
	form_class = EstateAgentForm
	template_name = "estate_agents/estate_agent_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Estate agent updated.")
		return resp

	def get_success_url(self):
		return reverse("estate_agents:detail", kwargs={"pk": self.object.pk})


class EstateAgentDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = EstateAgent
	success_url = reverse_lazy("estate_agents:list")

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Estate agent deleted.")
		return resp
