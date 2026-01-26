from __future__ import annotations

from django import forms

from apps.core.forms import BootstrapModelForm
from apps.documents.models import Document


class DocumentEditForm(BootstrapModelForm):
	class Meta:
		model = Document
		fields = ["title", "description"]


class DocumentUploadForm(BootstrapModelForm):
	"""
	Used from a business object's detail page.
	`content_type_id` and `object_id` are provided by the view/template.
	"""

	content_type_id = forms.IntegerField(widget=forms.HiddenInput())
	object_id = forms.IntegerField(widget=forms.HiddenInput())
	next = forms.CharField(required=False, widget=forms.HiddenInput())

	class Meta:
		model = Document
		fields = ["file", "title", "description"]
