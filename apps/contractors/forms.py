from __future__ import annotations

from apps.contacts.models import Contact
from apps.contractors.models import Contractor
from apps.core.forms import BootstrapModelForm


class ContractorForm(BootstrapModelForm):
	class Meta:
		model = Contractor
		fields = ["name", "trade", "email", "phone", "reference", "notes", "address", "contacts", "is_active"]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields["contacts"].queryset = Contact.objects.order_by("display_name")
		self.fields["contacts"].widget.attrs["size"] = 8
