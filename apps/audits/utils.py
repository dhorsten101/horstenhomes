from __future__ import annotations

from typing import Any

SENSITIVE_FIELD_NAMES = {
	"password", "passwd", "secret", "token", "api_key", "apikey",
	"access_token", "refresh_token", "private_key", "key",
}

REDACTED = "***REDACTED***"


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
		return value[:500] + "…"
	return value


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