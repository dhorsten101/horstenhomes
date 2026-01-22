from __future__ import annotations

from django.contrib import admin

from apps.audits.services import audit_log
from apps.audits.utils import model_diff


class AdminAuditMixin(admin.ModelAdmin):
	"""
	Drop-in mixin:
	  - logs add/change/delete from Django Admin
	  - includes field diffs on change
	"""
	
	audit_action_prefix = "admin"
	audit_exclude_fields = set()
	
	def save_model(self, request, obj, form, change):
		previous = None
		if change and obj.pk:
			try:
				previous = obj.__class__.objects.get(pk=obj.pk)
			except obj.__class__.DoesNotExist:
				previous = None
		
		super().save_model(request, obj, form, change)
		
		changes = {}
		if change and previous is not None:
			changes = model_diff(obj, previous)
			
			# allow opt-out fields
			for f in list(changes.keys()):
				if f in self.audit_exclude_fields:
					changes.pop(f, None)
		
		audit_log(
			action=f"{self.audit_action_prefix}.{'updated' if change else 'created'}",
			obj=obj,
			changes=changes,
			metadata={
				"app": obj._meta.app_label,
				"model": obj.__class__.__name__,
				"admin_path": request.path,
			},
		)
	
	def delete_model(self, request, obj):
		audit_log(
			action=f"{self.audit_action_prefix}.deleted",
			obj=obj,
			metadata={"app": obj._meta.app_label, "model": obj.__class__.__name__, "admin_path": request.path},
		)
		super().delete_model(request, obj)