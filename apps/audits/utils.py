from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db.models import Model

SENSITIVE_FIELD_NAMES = {
	"password", "passwd", "secret", "token", "api_key", "apikey",
	"access_token", "refresh_token", "private_key", "key",
}

REDACTED = "***REDACTED***"

def to_jsonable(value: Any) -> Any:
	"""
	Convert common Python/Django values to JSON-serializable primitives.
	This keeps AuditEvent JSONFields safe under psycopg JSON adaptation.
	"""
	if value is None or isinstance(value, (bool, int, float, str)):
		return value
	if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
		return value.isoformat()
	if isinstance(value, (Decimal, UUID)):
		return str(value)
	if isinstance(value, Model):
		return str(value)
	if isinstance(value, dict):
		return {str(k): to_jsonable(v) for k, v in value.items()}
	if isinstance(value, (list, tuple, set)):
		return [to_jsonable(v) for v in value]
	return str(value)


def is_sensitive_field(name: str) -> bool:
	n = (name or "").lower()
	if n in SENSITIVE_FIELD_NAMES:
		return True
	# catch patterns
	return any(x in n for x in ["password", "secret", "token", "key"])


def safe_value(field_name: str, value: Any) -> Any:
	if is_sensitive_field(field_name):
		return REDACTED
	# avoid dumping huge blobs
	if isinstance(value, str) and len(value) > 500:
		value = value[:500] + "…"
	return to_jsonable(value)


def model_diff(instance, previous) -> dict:
	"""
	Returns {"field": {"from": x, "to": y}, ...} (redacted where needed).
	"""
	if instance is None or previous is None:
		return {}
	
	changes: dict = {}
	for field in instance._meta.fields:
		name = field.name
		new = getattr(instance, name, None)
		old = getattr(previous, name, None)
		if new != old:
			changes[name] = {"from": safe_value(name, old), "to": safe_value(name, new)}
	return changes