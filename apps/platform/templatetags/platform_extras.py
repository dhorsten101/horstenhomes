from __future__ import annotations

import json

from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
	try:
		return mapping.get(key)
	except Exception:
		return None


@register.filter
def tojson(value):
	try:
		return json.dumps(value or {})
	except Exception:
		return "{}"

