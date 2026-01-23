from __future__ import annotations

from django import forms

from apps.contacts.models import Contact
from apps.core.forms import BootstrapModelForm


class ContactForm(BootstrapModelForm):
	tags = forms.JSONField(required=False, initial=list, help_text='JSON list, e.g. ["owner","tenant"]')

	class Meta:
		model = Contact
		fields = [
			"display_name",
			"email",
			"phone",
			"address",
			"external_id",
			"source",
			"tags",
		]

