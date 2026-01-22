from __future__ import annotations

from typing import Any, Optional

from django.db import transaction

from .middleware import get_audit_context
from .models import AuditEvent, AuditStatus


def _obj_meta(obj) -> tuple[str, str, str]:
	if obj is None:
		return "", "", ""
	cls = obj.__class__
	object_type = f"{cls._meta.app_label}.{cls.__name__}"
	object_id = str(getattr(obj, "pk", "") or "")
	object_repr = str(obj)[:300]
	return object_type, object_id, object_repr


def audit_log(
		*,
		action: str,
		obj: Optional[Any] = None,
		status: str = AuditStatus.SUCCESS,
		message: str = "",
		changes: Optional[dict] = None,
		metadata: Optional[dict] = None,
		# Overrides (system jobs, provisioning)
		actor_user_id: str = "",
		actor_email: str = "",
		tenant_schema: str = "",
		request_id: str = "",
		ip_address: Optional[str] = None,
		user_agent: str = "",
) -> None:
	"""
	Appends an audit event after the current DB transaction commits.
	Safe to call anywhere.
	"""
	ctx = get_audit_context()
	object_type, object_id, object_repr = _obj_meta(obj)
	
	payload = dict(
		action=action,
		status=status,
		message=(message or "")[:500],
		changes=changes or {},
		metadata=metadata or {},
		object_type=object_type,
		object_id=object_id,
		object_repr=object_repr,
		request_id=request_id or (ctx.request_id if ctx else ""),
		tenant_schema=tenant_schema or (ctx.tenant_schema if ctx else ""),
		actor_user_id=actor_user_id or (ctx.actor_user_id if ctx else ""),
		actor_email=actor_email or (ctx.actor_email if ctx else ""),
		ip_address=ip_address or (ctx.ip_address if ctx else None),
		user_agent=user_agent or (ctx.user_agent if ctx else ""),
	)
	
	def _write():
		AuditEvent.objects.create(**payload)
	
	transaction.on_commit(_write)