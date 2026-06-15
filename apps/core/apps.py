from django.apps import AppConfig


class CoreConfig(AppConfig):
	default_auto_field = "django.db.models.BigAutoField"
	name = "apps.core"

	def ready(self) -> None:
		from django import forms
		from django.contrib import admin
		from django.db import models

		_orig = admin.ModelAdmin.formfield_for_dbfield

		def formfield_for_dbfield(self, db_field, request, **kwargs):
			if isinstance(db_field, models.DateField):
				kwargs.setdefault(
					"widget",
					forms.DateInput(
						attrs={"type": "date", "class": "vDateField"},
						format="%Y-%m-%d",
					),
				)
			return _orig(self, db_field, request, **kwargs)

		admin.ModelAdmin.formfield_for_dbfield = formfield_for_dbfield
