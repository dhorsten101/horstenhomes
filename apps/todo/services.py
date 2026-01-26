from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.http import Http404


def is_allowed_todo_target(content_type: ContentType) -> bool:
	allowed = {
		("portfolio", "portfolio"),
		("properties", "property"),
		("properties", "unit"),
		("leases", "lease"),
		("contacts", "contact"),
		("addresses", "address"),
		("documents", "document"),
	}
	return (content_type.app_label, content_type.model) in allowed


def resolve_target_object(content_type_id: int, object_id: int) -> Any:
	ct = ContentType.objects.filter(pk=content_type_id).first()
	if ct is None or not is_allowed_todo_target(ct):
		raise Http404("Invalid target")

	Model = ct.model_class()
	if Model is None:
		raise Http404("Invalid target")

	try:
		return Model.objects.get(pk=object_id)
	except Model.DoesNotExist as e:  # type: ignore[attr-defined]
		raise Http404("Target not found") from e
