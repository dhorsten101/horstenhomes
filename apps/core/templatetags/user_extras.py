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

