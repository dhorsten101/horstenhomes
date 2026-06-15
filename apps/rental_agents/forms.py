from __future__ import annotations

from apps.core.agent_forms import ContactLinkedAgentForm
from apps.rental_agents.models import RentalAgent


class RentalAgentForm(ContactLinkedAgentForm):
	class Meta:
		model = RentalAgent
		fields = ["name", "contact", "reference", "notes", "is_active"]
