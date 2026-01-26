from __future__ import annotations

from apps.branding.models import TenantBranding
from apps.core.forms import BootstrapModelForm


class TenantBrandingForm(BootstrapModelForm):
	class Meta:
		model = TenantBranding
		fields = ["logo"]

