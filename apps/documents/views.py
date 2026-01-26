from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import PostOnlyDeleteMixin, TenantSchemaRequiredMixin
from apps.documents.forms import DocumentEditForm, DocumentUploadForm
from apps.documents.models import Document
from apps.documents.services import resolve_target_object


class DocumentListView(TenantSchemaRequiredMixin, LoginRequiredMixin, ListView):
	model = Document
	template_name = "documents/document_list.html"
	context_object_name = "documents"
	paginate_by = 25

	def get_queryset(self):
		return (
			Document.objects.select_related("content_type", "uploaded_by")
			.all()
			.order_by("-created_at")
		)


class DocumentDetailView(TenantSchemaRequiredMixin, LoginRequiredMixin, DetailView):
	model = Document
	template_name = "documents/document_detail.html"
	context_object_name = "document"

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ct = ContentType.objects.get_for_model(self.object, for_concrete_model=False)
		ctx["work_content_type_id"] = ct.id
		return ctx


class DocumentUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UpdateView):
	model = Document
	form_class = DocumentEditForm
	template_name = "documents/document_form.html"

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Document updated.")
		return resp

	def get_success_url(self):
		return reverse("documents:detail", kwargs={"pk": self.object.pk})


class DocumentDeleteView(TenantSchemaRequiredMixin, LoginRequiredMixin, PostOnlyDeleteMixin, DeleteView):
	model = Document
	success_url = reverse_lazy("documents:list")

	def delete(self, request, *args, **kwargs):
		messages.success(self.request, "Document deleted.")
		return super().delete(request, *args, **kwargs)


def _tenant_only(request: HttpRequest):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		raise Http404


@login_required
@require_POST
def document_upload_view(request: HttpRequest) -> HttpResponse:
	_tenant_only(request)
	form = DocumentUploadForm(request.POST, request.FILES)
	if not form.is_valid():
		messages.error(request, "Could not upload document. Please check the form.")
		return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or "/")

	content_type_id = int(form.cleaned_data["content_type_id"])
	object_id = int(form.cleaned_data["object_id"])
	target = resolve_target_object(content_type_id=content_type_id, object_id=object_id)
	ct = ContentType.objects.get_for_model(target, for_concrete_model=False)

	doc = Document.objects.create(
		content_type=ct,
		object_id=target.pk,
		file=form.cleaned_data["file"],
		title=form.cleaned_data.get("title", "") or "",
		description=form.cleaned_data.get("description", "") or "",
		uploaded_by=request.user,
	)

	messages.success(request, "Document uploaded.")
	return redirect(form.cleaned_data.get("next") or request.META.get("HTTP_REFERER") or reverse("documents:detail", kwargs={"pk": doc.pk}))


@login_required
def document_download_view(request: HttpRequest, pk: int) -> HttpResponse:
	_tenant_only(request)
	doc = get_object_or_404(Document, pk=pk)
	if not doc.file:
		raise Http404("No file")
	return FileResponse(doc.file.open("rb"), as_attachment=True, filename=doc.file.name.split("/")[-1])
