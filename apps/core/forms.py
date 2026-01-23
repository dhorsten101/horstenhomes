from __future__ import annotations

from django import forms


class BootstrapModelForm(forms.ModelForm):
	"""
	Lightweight Bootstrap 5 form styling without extra dependencies.
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for name, field in self.fields.items():
			w = field.widget
			classes = set((w.attrs.get("class") or "").split())

			if isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
				classes.add("form-check-input")
			elif isinstance(w, (forms.Select, forms.SelectMultiple)):
				classes.add("form-select")
			else:
				classes.add("form-control")

			w.attrs["class"] = " ".join(sorted(c for c in classes if c))

			# Helpful defaults
			if isinstance(w, forms.Textarea):
				w.attrs.setdefault("rows", 4)

