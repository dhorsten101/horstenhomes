from __future__ import annotations

from django import forms

from apps.core.forms import BootstrapModelForm
from apps.leases.models import Lease


class LeaseForm(BootstrapModelForm):
	tags = forms.JSONField(required=False, initial=list)

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
			"external_id",
			"source",
			"tags",
		]
		widgets = {
			"start_date": forms.DateInput(attrs={"type": "date"}),
			"end_date": forms.DateInput(attrs={"type": "date"}),
		}

