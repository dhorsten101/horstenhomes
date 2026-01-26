from django.contrib import admin

from apps.todo.models import TodoItem


@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
	list_display = ("id", "title", "status", "due_date", "assigned_to", "created_at")
	list_filter = ("status", "due_date", "content_type")
	search_fields = ("title", "description")
