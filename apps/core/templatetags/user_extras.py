from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def initials(value: str | None) -> str:
	"""
	Best-effort initials from a display name or email.
	Examples:
	  "Dean Horsten" -> "DH"
	  "dean@x.com"   -> "D"
	"""
	s = (value or "").strip()
	if not s:
		return ""
	# If it's an email, take the first letter of the local-part.
	if "@" in s:
		local = s.split("@", 1)[0].strip()
		return (local[:1] or "").upper()
	parts = [p for p in s.replace("-", " ").split() if p]
	if not parts:
		return s[:1].upper()
	if len(parts) == 1:
		return parts[0][:1].upper()
	return (parts[0][:1] + parts[-1][:1]).upper()


@register.inclusion_tag("components/crm_breadcrumb_nav.html")
def crm_breadcrumb_nav(*entries):
	"""Alternating label, url pairs; final label alone is the current page."""
	items = []
	i = 0
	while i < len(entries):
		label = entries[i]
		if i + 1 < len(entries) and entries[i + 1]:
			items.append({"label": label, "url": entries[i + 1]})
			i += 2
		else:
			items.append({"label": label, "url": None})
			i += 1
	parent_back = None
	for item in reversed(items[:-1]):
		if item.get("url"):
			parent_back = item
			break
	return {"items": items, "parent_back": parent_back}

