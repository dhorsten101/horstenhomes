from __future__ import annotations

from apps.core.agent_forms import ContactLinkedAgentForm
from apps.managing_agents.models import ManagingAgent


class ManagingAgentForm(ContactLinkedAgentForm):
	class Meta:
		model = ManagingAgent
		fields = ["name", "contact", "reference", "notes", "is_active"]
