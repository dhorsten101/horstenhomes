from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin
from apps.todo.forms import TodoCreateForm, TodoEditForm
from apps.todo.models import TodoItem, TodoStatus


class TodoListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = TodoItem
	template_name = "todo/todo_list.html"
	context_object_name = "todos"
	paginate_by = 50

	def get_queryset(self):
		status = (self.request.GET.get("status") or TodoStatus.OPEN).strip()
		qs = TodoItem.objects.select_related("assigned_to", "created_by", "content_type").all().order_by("-created_at")
		if status in (TodoStatus.OPEN, TodoStatus.DONE):
			qs = qs.filter(status=status)
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["status"] = (self.request.GET.get("status") or TodoStatus.OPEN).strip()
		return ctx


class TodoDetailView(TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = TodoItem
	template_name = "todo/todo_detail.html"
	context_object_name = "todo"


class TodoCreateView(TenantSchemaRequiredMixin, LoginRequiredMixin, CreateView):
	model = TodoItem
	form_class = TodoCreateForm
	template_name = "todo/todo_create.html"

	def form_valid(self, form):
		obj: TodoItem = form.save(commit=False)
		obj.created_by = self.request.user

		ct = form.cleaned_data.get("attach_to")
		obj_id = form.cleaned_data.get("attach_id")
		if ct and obj_id:
			obj.content_type = ct
			obj.object_id = int(obj_id)
		else:
			obj.content_type = None
			obj.object_id = None

		obj.save()
		messages.success(self.request, "Todo created.")
		return redirect("todo:detail", pk=obj.pk)


class TodoUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = TodoItem
	form_class = TodoEditForm
	template_name = "todo/todo_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Todo updated.")
		return resp

	def get_success_url(self):
		return reverse("todo:detail", kwargs={"pk": self.object.pk})


class TodoDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = TodoItem
	success_url = reverse_lazy("todo:list")

	def delete(self, request, *args, **kwargs):
		messages.success(self.request, "Todo deleted.")
		return super().delete(request, *args, **kwargs)


def _tenant_only(request: HttpRequest):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		raise Http404


@require_POST
@login_required
def todo_toggle_view(request: HttpRequest, pk: int) -> HttpResponse:
	_tenant_only(request)
	t = get_object_or_404(TodoItem, pk=pk)
	if t.status == TodoStatus.DONE:
		t.reopen()
		messages.success(request, "Todo reopened.")
	else:
		t.mark_done()
		messages.success(request, "Todo completed.")
	t.save(update_fields=["status", "completed_at"])
	return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("todo:detail", kwargs={"pk": t.pk}))
