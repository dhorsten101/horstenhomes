from __future__ import annotations

import os

from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedUUIDModel


def _tenant_logo_upload_to(instance: TenantBranding, filename: str) -> str:
	base, ext = os.path.splitext(filename)
	safe_base = slugify(base)[:80] or "logo"
	return f"tenant-branding/logo/{safe_base}{ext.lower()}"


class TenantBranding(TimeStampedUUIDModel):
	"""
	Tenant-local branding settings (stored in the tenant schema).
	Singleton row (enforced in views via get_or_create).
	"""

	logo = models.FileField(upload_to=_tenant_logo_upload_to, null=True, blank=True)

	# Theme presets: 3 slots, each with 4 colors:
	# - primary, secondary, body_bg, body_color
	themes = models.JSONField(default=dict, blank=True)
	active_theme = models.CharField(max_length=20, default="theme1", db_index=True)

	def get_theme(self) -> dict:
		defaults = {
			"theme1": {"primary": "#0d6efd", "secondary": "#6c757d", "body_bg": "#ffffff", "body_color": "#212529"},
			"theme2": {"primary": "#198754", "secondary": "#0dcaf0", "body_bg": "#ffffff", "body_color": "#212529"},
			"theme3": {"primary": "#6f42c1", "secondary": "#fd7e14", "body_bg": "#ffffff", "body_color": "#212529"},
		}
		merged = {**defaults, **(self.themes or {})}
		return merged.get(self.active_theme, merged["theme1"])

	def __str__(self) -> str:
		return "Tenant branding"


class UserThemePreference(TimeStampedUUIDModel):
	"""
	Tenant-user preference: which theme slot to use (does not change colors).
	Stored in the tenant schema.
	"""

	user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="theme_pref")
	theme_key = models.CharField(max_length=20, default="theme1", db_index=True)

	def __str__(self) -> str:
		return f"{self.user} → {self.theme_key}"

