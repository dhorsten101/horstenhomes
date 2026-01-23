from __future__ import annotations

from django import forms

from apps.core.forms import BootstrapModelForm
from apps.properties.models import Property, Unit


class PropertyForm(BootstrapModelForm):
	tags = forms.JSONField(required=False, initial=list, help_text='JSON list, e.g. ["kzn","block-a"]')

	class Meta:
		model = Property
		fields = [
			"portfolio",
			"name",
			"property_type",
			"address",
			"is_archived",
			"external_id",
			"source",
			"tags",
		]


class UnitForm(BootstrapModelForm):
	tags = forms.JSONField(required=False, initial=list)

	class Meta:
		model = Unit
		fields = [
			"property",
			"unit_number",
			"floor",
			"bedrooms",
			"bathrooms",
			"size_m2",
			"status",
			"external_id",
			"source",
			"tags",
		]

