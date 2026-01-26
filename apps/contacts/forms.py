from __future__ import annotations

from apps.contacts.models import Contact
from apps.core.forms import BootstrapModelForm


class ContactForm(BootstrapModelForm):
	class Meta:
		model = Contact
		fields = [
			"display_name",
			"email",
			"phone",
			"address",
		]

