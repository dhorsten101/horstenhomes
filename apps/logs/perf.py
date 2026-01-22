from __future__ import annotations

import logging
import time
from contextlib import ContextDecorator

from django.conf import settings
from django.db import connection


def _slow_request_ms() -> int:
	return int(getattr(settings, "SLOW_REQUEST_MS", 1000))


def _slow_db_query_ms() -> int:
	return int(getattr(settings, "SLOW_DB_QUERY_MS", 200))


class DBQueryLogger(ContextDecorator):
	"""
	Per-request query logger using connection.execute_wrapper.
	Logs:
	- slow queries (> SLOW_DB_QUERY_MS)
	- query errors (ERROR)
	"""

	def __init__(self):
		self._cm = None

	def __enter__(self):
		threshold = _slow_db_query_ms()
		log = logging.getLogger("db.query")

		def wrapper(execute, sql, params, many, context):
			start = time.perf_counter()
			try:
				return execute(sql, params, many, context)
			except Exception:
				dur_ms = int((time.perf_counter() - start) * 1000)
				log.exception(
					"DB query failed",
					extra={"duration_ms": dur_ms, "sql": str(sql)[:2000]},
				)
				raise
			finally:
				dur_ms = int((time.perf_counter() - start) * 1000)
				if dur_ms >= threshold:
					log.warning(
						"Slow DB query",
						extra={"duration_ms": dur_ms, "sql": str(sql)[:2000]},
					)

		self._cm = connection.execute_wrapper(wrapper)
		return self._cm.__enter__()

	def __exit__(self, exc_type, exc, tb):
		if self._cm:
			return self._cm.__exit__(exc_type, exc, tb)
		return False


def log_slow_request(method: str, path: str, duration_ms: int, status_code: int):
	if duration_ms < _slow_request_ms():
		return
	logging.getLogger("web.request").warning(
		"Slow request",
		extra={"duration_ms": duration_ms, "status_code": status_code, "method": method, "path": path},
	)

