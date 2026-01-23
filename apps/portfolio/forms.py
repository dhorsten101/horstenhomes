from __future__ import annotations

from django import forms

from apps.core.forms import BootstrapModelForm
from apps.portfolio.models import Portfolio


class PortfolioForm(BootstrapModelForm):
	tags = forms.JSONField(required=False, initial=list, help_text='JSON list, e.g. ["family","commercial"]')

	class Meta:
		model = Portfolio
		fields = [
			"name",
			"description",
			"owner_contact",
			"is_archived",
			"tags",
		]

