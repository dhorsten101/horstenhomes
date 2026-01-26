from __future__ import annotations

from django import forms


class TenantThemeForm(forms.Form):
	active_theme = forms.ChoiceField(
		choices=[("theme1", "Theme 1"), ("theme2", "Theme 2"), ("theme3", "Theme 3")],
	)
	primary = forms.CharField()
	secondary = forms.CharField()
	body_bg = forms.CharField()
	body_color = forms.CharField()

	def clean(self):
		cleaned = super().clean()
		for k in ("primary", "secondary", "body_bg", "body_color"):
			val = (cleaned.get(k) or "").strip()
			if not val.startswith("#") or len(val) not in (4, 7):
				raise forms.ValidationError("Colors must be hex values like #0d6efd.")
			cleaned[k] = val
		return cleaned

