from __future__ import annotations

from apps.core.agent_forms import ContactLinkedAgentForm
from apps.estate_agents.models import EstateAgent


class EstateAgentForm(ContactLinkedAgentForm):
	class Meta:
		model = EstateAgent
		fields = ["name", "contact", "reference", "notes", "is_active"]
