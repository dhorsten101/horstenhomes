from __future__ import annotations

from apps.branding.models import TenantBranding, UserThemePreference


def tenant_branding(request):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		return {"tenant_branding": None, "tenant_theme": None, "tenant_theme_key": None}
	try:
		b = TenantBranding.objects.first()
		if not b:
			return {"tenant_branding": None, "tenant_theme": None, "tenant_theme_key": None}

		theme_key = b.active_theme
		user = getattr(request, "user", None)
		if user and getattr(user, "is_authenticated", False):
			pref = UserThemePreference.objects.filter(user=user).first()
			if pref and pref.theme_key:
				theme_key = pref.theme_key

		# Use model helper for defaults+merge; temporarily override active_theme selection.
		orig = b.active_theme
		b.active_theme = theme_key
		try:
			theme = b.get_theme()
		finally:
			b.active_theme = orig

		return {"tenant_branding": b, "tenant_theme": theme, "tenant_theme_key": theme_key}
	except Exception:
		return {"tenant_branding": None, "tenant_theme": None, "tenant_theme_key": None}

