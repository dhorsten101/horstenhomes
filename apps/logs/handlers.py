from __future__ import annotations

import logging
import threading
import sys
from typing import Any

from django.apps import apps as django_apps
from django.conf import settings
from django.utils import timezone

try:
	# Reuse audit context if present (request id, tenant schema, actor, etc.)
	from apps.audits.middleware import get_audit_context
except Exception:  # pragma: no cover
	get_audit_context = None

try:
	from apps.audits.utils import to_jsonable
except Exception:  # pragma: no cover
	def to_jsonable(value: Any) -> Any:  # type: ignore
		return value


_tls = threading.local()


class DatabaseLogHandler(logging.Handler):
	"""
	Persists Python logging records to the database (per schema).

	Important:
	- Never raise from emit() (logging must not crash the app)
	- Prevent recursion if DB write triggers logging
	"""

	def emit(self, record: logging.LogRecord) -> None:
		if getattr(_tls, "in_emit", False):
			return
		_tls.in_emit = True
		try:
			if not django_apps.ready:
				return

			from apps.logs.models import LogEntry

			ctx = get_audit_context() if get_audit_context else None

			exc_text = ""
			if record.exc_info:
				try:
					exc_text = self.formatException(record.exc_info)
				except Exception:
					exc_text = ""

			# Capture structured "extra" data safely.
			standard = {
				"name","msg","args","levelname","levelno","pathname","filename","module","exc_info","exc_text",
				"stack_info","lineno","funcName","created","msecs","relativeCreated","thread","threadName",
				"processName","process","message",
			}
			record_extras = {k: v for k, v in record.__dict__.items() if k not in standard}
			extra = {
				"args": to_jsonable(getattr(record, "args", None)),
				"stack_info": to_jsonable(getattr(record, "stack_info", None)),
				**to_jsonable(record_extras),
			}

			LogEntry.objects.create(
				created_at=timezone.now(),
				level=record.levelname,
				logger=record.name,
				message=str(record.getMessage()),
				pathname=getattr(record, "pathname", "") or "",
				lineno=getattr(record, "lineno", None),
				func_name=getattr(record, "funcName", "") or "",
				module=getattr(record, "module", "") or "",
				process=getattr(record, "process", None),
				thread=getattr(record, "thread", None),
				exc_text=exc_text[:10000],
				request_id=(ctx.request_id if ctx else ""),
				tenant_schema=(ctx.tenant_schema if ctx else ""),
				request_method=(ctx.request_method if ctx else ""),
				request_path=(ctx.request_path if ctx else ""),
				actor_user_id=(ctx.actor_user_id if ctx else ""),
				actor_email=(ctx.actor_email if ctx else ""),
				ip_address=(ctx.ip_address if ctx else None),
				user_agent=(ctx.user_agent if ctx else ""),
				extra=to_jsonable(extra),
			)
		except Exception as e:
			# Keep some breadcrumbs in DEBUG so we can diagnose handler issues.
			if getattr(settings, "DEBUG", False):
				try:
					print(f"[DatabaseLogHandler] failed: {type(e).__name__}: {e}", file=sys.stderr)
				except Exception:
					pass
			# Never let logging break request handling.
			return
		finally:
			_tls.in_emit = False

