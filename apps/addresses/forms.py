from __future__ import annotations

from apps.addresses.models import Address
from apps.core.forms import BootstrapModelForm


class AddressForm(BootstrapModelForm):
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
		]

