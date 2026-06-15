from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin
from apps.managing_agents.forms import ManagingAgentForm
from apps.managing_agents.models import ManagingAgent


def _agent_queryset():
	return ManagingAgent.objects.select_related("contact", "contact__address")


class ManagingAgentListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = ManagingAgent
	template_name = "managing_agents/managing_agent_list.html"
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


class ManagingAgentDetailView(TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = ManagingAgent
	template_name = "managing_agents/managing_agent_detail.html"
	context_object_name = "agent"

	def get_queryset(self):
		return _agent_queryset()


class ManagingAgentCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = ManagingAgent
	form_class = ManagingAgentForm
	template_name = "managing_agents/managing_agent_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Managing agent created.")
		return resp

	def get_success_url(self):
		return reverse("managing_agents:detail", kwargs={"pk": self.object.pk})


class ManagingAgentUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = ManagingAgent
	form_class = ManagingAgentForm
	template_name = "managing_agents/managing_agent_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Managing agent updated.")
		return resp

	def get_success_url(self):
		return reverse("managing_agents:detail", kwargs={"pk": self.object.pk})


class ManagingAgentDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = ManagingAgent
	success_url = reverse_lazy("managing_agents:list")

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Managing agent deleted.")
		return resp
