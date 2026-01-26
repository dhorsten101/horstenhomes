from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.base import ContextMixin


class TenantSchemaRequiredMixin(ContextMixin):
	"""
	Ensure views only render for tenant schemas (not public/control-plane schema).
	"""

	def dispatch(self, request, *args, **kwargs):
		tenant = getattr(request, "tenant", None)
		if not tenant or getattr(tenant, "schema_name", None) == "public":
			# Public website (www/admin host). Tenant CRM views should not hard-404;
			# redirect to the marketing landing/home instead.
			try:
				return redirect("landing")
			except Exception:
				return redirect("home")
		return super().dispatch(request, *args, **kwargs)


class PostOnlyDeleteMixin:
	"""
	Make DeleteViews POST-only so list pages can use SweetAlert confirmation
	with a POST form (no intermediate confirm page).
	"""

	def get(self, request, *args, **kwargs):  # pragma: no cover
		return HttpResponse(status=405)


class WorkItemContextMixin(ContextMixin):
	"""
	Add Documents context for DetailViews.

	Exposes:
	- work_content_type_id
	- work_object_id
	- work_documents
	- upload form
	"""

	def get_work_object(self):
		return getattr(self, "object", None)

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		obj = self.get_work_object()
		if obj is None:
			return ctx

		from django.contrib.contenttypes.models import ContentType

		from apps.documents.forms import DocumentUploadForm
		from apps.documents.models import Document

		ct = ContentType.objects.get_for_model(obj, for_concrete_model=False)
		ctx["work_content_type_id"] = ct.id
		ctx["work_object_id"] = obj.pk

		ctx["work_documents"] = (
			Document.objects.filter(content_type=ct, object_id=obj.pk)
			.select_related("uploaded_by")
			.order_by("-created_at")[:25]
		)

		ctx["document_upload_form"] = DocumentUploadForm(
			initial={"content_type_id": ct.id, "object_id": obj.pk, "next": self.request.get_full_path()}
		)

		return ctx

