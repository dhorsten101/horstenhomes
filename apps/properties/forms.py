from __future__ import annotations

from django import forms

from apps.core.forms import BootstrapModelForm
from apps.entitlements.services import QUOTA_MAX_UNITS, enforce_quota
from apps.properties.models import Property, Unit


class PropertyForm(BootstrapModelForm):
	class Meta:
		model = Property
		fields = [
			"portfolio",
			"name",
			"property_type",
			"purchase_date",
			"previous_purchase_price",
			"purchase_price",
			"address",
			"is_archived",
		]

		widgets = {
			"purchase_date": forms.DateInput(attrs={"type": "date"}),
		}


class UnitForm(BootstrapModelForm):
	def __init__(self, *args, request=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.request = request

	def clean(self):
		cleaned = super().clean()

		# Enforce billing quota on a per-unit basis.
		# - soft mode: allow creation but record an audit event
		# - hard mode: block with ValidationError
		if self.instance and self.instance.pk:
			return cleaned

		tenant = getattr(getattr(self, "request", None), "tenant", None)
		if not tenant or getattr(tenant, "schema_name", None) == "public":
			return cleaned

		used_units = Unit.objects.count()
		try:
			enforce_quota(
				tenant,
				key=QUOTA_MAX_UNITS,
				used=used_units,
				needed=1,
				action="quota.max_units.exceeded",
				obj=None,
				metadata={"model": "properties.Unit"},
			)
		except Exception as e:
			raise forms.ValidationError(str(e)) from e

		return cleaned

	class Meta:
		model = Unit
		fields = [
			"property",
			"unit_number",
			"floor",
			"bedrooms",
			"bathrooms",
			"size_m2",
			"purchase_price",
			"status",
		]

