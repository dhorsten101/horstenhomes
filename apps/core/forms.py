from __future__ import annotations

from django import forms

_ISO_DATE_FORMAT = "%Y-%m-%d"


def apply_date_picker_widgets(form: forms.BaseForm) -> None:
	"""Use native click-to-select date inputs for all DateField widgets."""
	for field in form.fields.values():
		if not isinstance(field, forms.DateField):
			continue
		attrs = dict(getattr(field.widget, "attrs", {}) or {})
		attrs["type"] = "date"
		field.widget = forms.DateInput(attrs=attrs, format=_ISO_DATE_FORMAT)


def apply_address_field_widgets(form: forms.BaseForm) -> list[str]:
	"""Configure ModelChoiceFields for Address and return their field names."""
	from apps.addresses.models import Address

	names: list[str] = []
	for name, field in form.fields.items():
		if not isinstance(field, forms.ModelChoiceField):
			continue
		try:
			if field.queryset.model is not Address:
				continue
		except AttributeError:
			continue
		field.queryset = Address.objects.order_by("line1", "city")
		field.empty_label = "Select an address…"
		names.append(name)
	return names


class BootstrapModelForm(forms.ModelForm):
	"""
	Lightweight Bootstrap 5 form styling without extra dependencies.
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		apply_date_picker_widgets(self)
		self.address_field_names = apply_address_field_widgets(self)
		for _name, field in self.fields.items():
			w = field.widget
			classes = set((w.attrs.get("class") or "").split())

			if isinstance(w, forms.CheckboxInput | forms.CheckboxSelectMultiple):
				classes.add("form-check-input")
			elif isinstance(w, forms.Select | forms.SelectMultiple):
				classes.add("form-select")
			else:
				classes.add("form-control")

			w.attrs["class"] = " ".join(sorted(c for c in classes if c))

			# Helpful defaults
			if isinstance(w, forms.Textarea):
				w.attrs.setdefault("rows", 4)
