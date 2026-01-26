from __future__ import annotations

import time
import traceback

from django.utils.deprecation import MiddlewareMixin

from apps.audits.models import AuditStatus
from apps.audits.services import audit_log
from apps.logs.perf import DBQueryLogger, log_slow_request


class ExceptionAlertMiddleware(MiddlewareMixin):
	"""
	Central exception -> alert capture.

	We write an audit event immediately (defer=False) so it is not lost if the
	request transaction rolls back.
	"""

	def process_exception(self, request, exception):
		try:
			audit_log(
				action="error.unhandled_exception",
				status=AuditStatus.FAILURE,
				message=f"{type(exception).__name__}: {exception}",
				metadata={"traceback": traceback.format_exc()[-10000:]},
				defer=False,
			)
		except Exception:
			# Never break exception handling
			return None
		return None


class PerformanceAlertMiddleware(MiddlewareMixin):
	"""
	- Measures request duration and logs slow requests (warning)
	- Captures slow DB queries per request
	"""

	def process_request(self, request):
		request._perf_start = time.perf_counter()
		request._db_query_logger = DBQueryLogger()
		request._db_query_logger.__enter__()

	def process_response(self, request, response):
		logger = getattr(request, "_db_query_logger", None)
		if logger is not None:
			try:
				logger.__exit__(None, None, None)
			except Exception:
				pass

		start = getattr(request, "_perf_start", None)
		if start is not None:
			dur_ms = int((time.perf_counter() - start) * 1000)
			log_slow_request(getattr(request, "method", ""), getattr(request, "path", ""), dur_ms, getattr(response, "status_code", 0))

		# Turn 5xx responses into alerts even if they were handled.
		if getattr(response, "status_code", 0) >= 500:
			try:
				audit_log(
					action="error.http_5xx",
					status=AuditStatus.FAILURE,
					message=f"HTTP {response.status_code}",
					metadata={"path": getattr(request, "path", ""), "method": getattr(request, "method", "")},
					defer=False,
				)
			except Exception:
				pass

		return response

	def process_exception(self, request, exception):
		logger = getattr(request, "_db_query_logger", None)
		if logger is not None:
			try:
				logger.__exit__(type(exception), exception, exception.__traceback__)
			except Exception:
				pass
		return None

