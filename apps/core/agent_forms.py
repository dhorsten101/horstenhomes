from __future__ import annotations

from apps.contacts.models import Contact
from apps.core.forms import BootstrapModelForm


class ContactLinkedAgentForm(BootstrapModelForm):
	"""Agent form: pick an existing contact; agent-specific fields only."""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields["contact"].queryset = Contact.objects.select_related("address").order_by("display_name")
		self.fields["contact"].empty_label = "Select a contact…"
