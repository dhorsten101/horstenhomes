from __future__ import annotations

from apps.core.forms import BootstrapModelForm
from apps.portfolio.models import Portfolio


class PortfolioForm(BootstrapModelForm):
	class Meta:
		model = Portfolio
		fields = [
			"name",
			"description",
			"owner_contact",
			"is_archived",
		]

