from __future__ import annotations

from django.http import Http404, HttpResponse
from django.views.generic.base import ContextMixin


class TenantSchemaRequiredMixin(ContextMixin):
	"""
	Ensure views only render for tenant schemas (not public/control-plane schema).
	"""

	def dispatch(self, request, *args, **kwargs):
		tenant = getattr(request, "tenant", None)
		if not tenant or getattr(tenant, "schema_name", None) == "public":
			raise Http404()
		return super().dispatch(request, *args, **kwargs)


class PostOnlyDeleteMixin:
	"""
	Make DeleteViews POST-only so list pages can use SweetAlert confirmation
	with a POST form (no intermediate confirm page).
	"""

	def get(self, request, *args, **kwargs):  # pragma: no cover
		return HttpResponse(status=405)

