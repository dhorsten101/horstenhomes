from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType

from apps.activity.models import ActivityEvent, Note, Tag, TaggedItem
from apps.audits.middleware import get_audit_context
from apps.audits.utils import to_jsonable


def _content_type_for(obj: Any) -> ContentType:
	return ContentType.objects.get_for_model(obj.__class__)


def add_note(*, obj: Any, body: str) -> Note:
	ctx = get_audit_context()
	return Note.objects.create(
		content_type=_content_type_for(obj),
		object_id=str(getattr(obj, "pk", "")),
		body=body,
		actor_user_id=(ctx.actor_user_id if ctx else ""),
		actor_email=(ctx.actor_email if ctx else ""),
		request_id=(ctx.request_id if ctx else ""),
	)


def add_tag(*, obj: Any, tag_name: str, color: str = "") -> TaggedItem:
	tag, _ = Tag.objects.get_or_create(name=tag_name.strip(), defaults={"color": color})
	return TaggedItem.objects.get_or_create(
		tag=tag,
		content_type=_content_type_for(obj),
		object_id=str(getattr(obj, "pk", "")),
	)[0]


def log_activity(
	*,
	obj: Any,
	verb: str,
	message: str = "",
	metadata: dict | None = None,
) -> ActivityEvent:
	ctx = get_audit_context()
	return ActivityEvent.objects.create(
		verb=verb,
		message=message[:500],
		metadata=to_jsonable(metadata or {}),
		content_type=_content_type_for(obj),
		object_id=str(getattr(obj, "pk", "")),
		actor_user_id=(ctx.actor_user_id if ctx else ""),
		actor_email=(ctx.actor_email if ctx else ""),
		request_id=(ctx.request_id if ctx else ""),
	)

