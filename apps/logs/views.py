from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.audits.middleware import get_audit_context
from apps.audits.utils import to_jsonable
from apps.logs.models import LogEntry


@csrf_exempt
def client_log_view(request: HttpRequest) -> HttpResponse:
	"""
	Frontend/browser logging endpoint.
	Accepts JSON: { level, message, ... } and writes a LogEntry.

	Note: CSRF-exempt so it can capture errors pre-login. Keep payload small.
	"""
	if request.method != "POST":
		return HttpResponse(status=405)

	try:
		body = request.body.decode("utf-8") if request.body else ""
		# hard cap to avoid abuse
		if len(body) > 50_000:
			return JsonResponse({"ok": False, "error": "payload_too_large"}, status=413)
		data: dict[str, Any] = json.loads(body or "{}")
	except Exception:
		return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

	level = str(data.get("level") or "ERROR").upper()[:10]
	if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
		level = "ERROR"

	message = str(data.get("message") or "")[:5000]
	if not message:
		return JsonResponse({"ok": False, "error": "missing_message"}, status=400)

	ctx = get_audit_context()
	extra = to_jsonable({k: v for k, v in data.items() if k not in {"level", "message"}})

	LogEntry.objects.create(
		level=level,
		logger="frontend",
		message=message,
		pathname="",
		lineno=None,
		func_name="",
		module="",
		process=None,
		thread=None,
		exc_text=str(data.get("stack") or "")[:10000],
		request_id=(ctx.request_id if ctx else ""),
		tenant_schema=(ctx.tenant_schema if ctx else ""),
		request_method=(ctx.request_method if ctx else ""),
		request_path=(ctx.request_path if ctx else ""),
		actor_user_id=(ctx.actor_user_id if ctx else ""),
		actor_email=(ctx.actor_email if ctx else ""),
		ip_address=(ctx.ip_address if ctx else None),
		user_agent=(ctx.user_agent if ctx else ""),
		extra=extra,
	)

	return JsonResponse({"ok": True})
