from django.contrib import admin

from apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
	list_display = ("id", "title", "content_type", "object_id", "uploaded_by", "created_at")
	list_filter = ("content_type",)
	search_fields = ("title", "description", "file")
