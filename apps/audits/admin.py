from django.contrib import admin
from .models import AuditEvent

from apps.audits.admin_mixins import AdminAuditMixin


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
	list_display = (
		"created_at",
		"tenant_schema",
		"request_method",
		"request_path",
		"action",
		"status",
		"actor_email",
		"object_type",
		"object_id",
	)
	list_filter = ("status", "action", "tenant_schema")
	search_fields = ("action", "actor_email", "object_type", "object_id", "request_id", "request_path", "message")
	date_hierarchy = "created_at"
	readonly_fields = [f.name for f in AuditEvent._meta.fields]
	
	def has_add_permission(self, request):
		return False
	
	def has_change_permission(self, request, obj=None):
		return False