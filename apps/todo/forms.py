from __future__ import annotations

from django import forms
from django.contrib.contenttypes.models import ContentType

from apps.core.forms import BootstrapModelForm
from apps.todo.models import TodoItem
from apps.todo.services import is_allowed_todo_target, resolve_target_object


class TodoCreateForm(BootstrapModelForm):
	"""
	Global create form:
	- always creates a TodoItem
	- optionally attaches it to another object (content_type + object_id)
	"""

	attach_to = forms.ModelChoiceField(
		required=False,
		queryset=ContentType.objects.none(),
		help_text="Optional: select what this todo is for.",
	)
	attach_id = forms.IntegerField(
		required=False,
		help_text="Optional: enter the ID of the item selected above.",
	)

	class Meta:
		model = TodoItem
		fields = ["title", "description", "due_date", "assigned_to"]
		widgets = {
			"due_date": forms.DateInput(attrs={"type": "date"}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Limit attach targets to allowed business models (+ documents)
		all_cts = ContentType.objects.all()
		allowed_ids = [ct.id for ct in all_cts if is_allowed_todo_target(ct)]
		self.fields["attach_to"].queryset = (
			ContentType.objects.filter(id__in=allowed_ids).order_by("app_label", "model")
		)

	def clean(self):
		cleaned = super().clean()
		ct = cleaned.get("attach_to")
		obj_id = cleaned.get("attach_id")

		if ct and not obj_id:
			raise forms.ValidationError("If you select an attach target, you must enter an ID.")
		if obj_id and not ct:
			raise forms.ValidationError("If you enter an attach ID, you must select an attach target.")

		if ct and obj_id:
			# Validate target exists and is allowed
			try:
				resolve_target_object(content_type_id=ct.id, object_id=int(obj_id))
			except Exception:
				raise forms.ValidationError("That attached item was not found.") from None

		return cleaned


class TodoEditForm(BootstrapModelForm):
	class Meta:
		model = TodoItem
		fields = ["title", "description", "due_date", "assigned_to", "status"]
		widgets = {
			"due_date": forms.DateInput(attrs={"type": "date"}),
		}
