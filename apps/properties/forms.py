from __future__ import annotations

from django import forms
from django.db.models import Q

from apps.core.forms import BootstrapModelForm
from apps.entitlements.services import QUOTA_MAX_UNITS, enforce_quota
from apps.estate_agents.models import EstateAgent
from apps.managing_agents.models import ManagingAgent
from apps.properties.models import Property, Unit
from apps.rental_agents.models import RentalAgent


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


class UnitForm(BootstrapModelForm):
	def __init__(self, *args, request=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.request = request
		if self.instance and self.instance.pk:
			self.fields.pop("managing_agent_reference", None)
		for field_name, model in (
			("estate_agent", EstateAgent),
			("managing_agent", ManagingAgent),
			("rental_agent", RentalAgent),
		):
			qs = model.objects.filter(is_active=True)
			if self.instance and self.instance.pk:
				current_id = getattr(self.instance, f"{field_name}_id", None)
				if current_id:
					qs = model.objects.filter(Q(is_active=True) | Q(pk=current_id))
			self.fields[field_name].queryset = qs.select_related("contact").order_by("name")
			self.fields[field_name].required = False

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
			"purchase_date",
			"purchase_price",
			"municipal_reference",
			"managing_agent_reference",
			"estate_agent",
			"managing_agent",
			"rental_agent",
			"status",
		]

