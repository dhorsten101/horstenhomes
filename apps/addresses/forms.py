from __future__ import annotations

from django import forms

from apps.addresses.models import Address
from apps.core.forms import BootstrapModelForm


class AddressForm(BootstrapModelForm):
	tags = forms.JSONField(required=False, initial=list, help_text='JSON list, e.g. ["kzn","office"]')

	class Meta:
		model = Address
		fields = [
			"label",
			"line1",
			"line2",
			"city",
			"region",
			"postal_code",
			"country",
			"lat",
			"lng",
			"tags",
		]

