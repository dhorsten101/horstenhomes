from __future__ import annotations

from django.http import HttpResponse

from apps.entitlements.services import QUOTA_API_REQUESTS_PER_DAY, get_tenant_by_schema, increment_and_enforce


class ApiQuotaMiddleware:
	"""
	API rate limit hooks (per-tenant).

	This is deliberately simple and safe:
	- only counts paths starting with /api/ (by default)
	- soft mode: allows but logs/audits via entitlements service
	- hard mode: returns 429 when over quota
	"""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		# Only count API-ish routes (avoid billing normal HTML pages by default)
		path = getattr(request, "path", "") or ""
		if not path.startswith("/api/"):
			return self.get_response(request)

		tenant = getattr(request, "tenant", None)
		schema = getattr(tenant, "schema_name", "") if tenant else ""
		tenant_row = get_tenant_by_schema(schema)
		if not tenant_row:
			return self.get_response(request)

		try:
			increment_and_enforce(
				tenant_row,
				key=QUOTA_API_REQUESTS_PER_DAY,
				period="day",
				action="quota.api_requests_per_day.exceeded",
				obj=None,
				metadata={"path": path, "method": getattr(request, "method", "")},
				delta=1,
			)
		except Exception:
			# Hard mode can raise; for API routes we translate into 429.
			return HttpResponse("API quota exceeded.", status=429)

		return self.get_response(request)

