from django.contrib import admin

from apps.logs.models import LogEntry


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
	list_display = ("created_at", "tenant_schema", "level", "logger", "request_method", "request_path")
	list_filter = ("level", "logger", "tenant_schema")
	search_fields = ("message", "logger", "request_id", "request_path", "actor_email")
	date_hierarchy = "created_at"
	readonly_fields = [f.name for f in LogEntry._meta.fields]

	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		return False
