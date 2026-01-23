from django.contrib import admin

from apps.activity.models import ActivityEvent, Note, Tag, TaggedItem


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ("name", "color", "created_at")
	search_fields = ("name",)


@admin.register(TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
	list_display = ("created_at", "tag", "content_type", "object_id")
	list_filter = ("tag", "content_type")
	search_fields = ("object_id",)
	readonly_fields = [f.name for f in TaggedItem._meta.fields]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
	list_display = ("created_at", "content_type", "object_id", "actor_email")
	list_filter = ("content_type",)
	search_fields = ("object_id", "actor_email", "body")
	readonly_fields = [f.name for f in Note._meta.fields]


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
	list_display = ("created_at", "verb", "content_type", "object_id", "actor_email")
	list_filter = ("verb", "content_type")
	search_fields = ("verb", "object_id", "actor_email", "message")
	readonly_fields = [f.name for f in ActivityEvent._meta.fields]

