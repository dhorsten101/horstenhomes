from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from django.utils.deprecation import MiddlewareMixin

try:
	# django-tenants
	from django_tenants.utils import get_tenant
except Exception:
	get_tenant = None


@dataclass(frozen=True)
class AuditContext:
	request_id: str
	ip_address: Optional[str]
	user_agent: str
	tenant_schema: str
	actor_user_id: str
	actor_email: str


_audit_ctx: ContextVar[Optional[AuditContext]] = ContextVar("audit_ctx", default=None)


def get_audit_context() -> Optional[AuditContext]:
	return _audit_ctx.get()


class AuditContextMiddleware(MiddlewareMixin):
	"""
	Must run AFTER TenantMainMiddleware (so tenant is resolved),
	and BEFORE your app code writes audit logs.
	"""
	
	def process_request(self, request):
		request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
		
		# Best-effort IP extraction (dev/proxy safe)
		xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
		ip = (xff.split(",")[0].strip() if xff else None) or request.META.get("REMOTE_ADDR")
		
		ua = request.META.get("HTTP_USER_AGENT", "")[:2000]
		
		tenant_schema = ""
		if get_tenant is not None:
			try:
				tenant = getattr(request, "tenant", None) or get_tenant(request)
				tenant_schema = getattr(tenant, "schema_name", "") or ""
			except Exception:
				tenant_schema = ""
		
		user = getattr(request, "user", None)
		actor_user_id = str(getattr(user, "pk", "")) if getattr(user, "is_authenticated", False) else ""
		actor_email = str(getattr(user, "email", "")) if getattr(user, "is_authenticated", False) else ""
		
		_audit_ctx.set(
			AuditContext(
				request_id=request_id,
				ip_address=ip,
				user_agent=ua,
				tenant_schema=tenant_schema,
				actor_user_id=actor_user_id,
				actor_email=actor_email,
			)
		)
		
		# Optional: expose request_id in response for debugging
		request.audit_request_id = request_id
	
	def process_response(self, request, response):
		rid = getattr(request, "audit_request_id", None)
		if rid:
			response["X-Request-ID"] = rid
		return response