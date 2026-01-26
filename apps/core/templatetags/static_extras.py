from __future__ import annotations

import os
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()

# Note: Adding/renaming template tag modules may require a dev server reload.

@register.simple_tag
def static_v(path: str) -> str:
	"""
	Versioned static URL using file mtime (dev-friendly cache busting).
	Falls back to plain `{% static %}` if the file can't be stat'd.
	"""
	url = static(path)
	try:
		base = Path(getattr(settings, "BASE_DIR", Path(".")))
		full = base / "static" / path
		mtime = int(os.path.getmtime(full))
		sep = "&" if "?" in url else "?"
		return f"{url}{sep}v={mtime}"
	except Exception:
		return url

