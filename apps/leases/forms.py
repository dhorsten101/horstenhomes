from __future__ import annotations

from apps.core.forms import BootstrapModelForm
from apps.leases.models import Lease


class LeaseForm(BootstrapModelForm):
	class Meta:
		model = Lease
		fields = [
			"unit",
			"primary_tenant",
			"status",
			"start_date",
			"end_date",
			"rent_amount",
			"deposit_amount",
			"billing_day",
		]

