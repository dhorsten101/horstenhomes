from __future__ import annotations

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.audits.services import audit_log
from apps.audits.utils import model_diff

# Set of "app_label.ModelName"
AUDIT_MODEL_ALLOWLIST: set[str] = set()

_previous: dict[tuple[str, str], object] = {}


def register_model(model_class):
	AUDIT_MODEL_ALLOWLIST.add(f"{model_class._meta.app_label}.{model_class.__name__}")


@receiver(pre_save)
def capture_previous(sender, instance, **kwargs):
	key = f"{getattr(sender, '_meta', None) and sender._meta.app_label}.{getattr(sender, '__name__', '')}"
	if key not in AUDIT_MODEL_ALLOWLIST:
		return
	if not getattr(instance, "pk", None):
		return
	try:
		_previous[(key, str(instance.pk))] = sender.objects.get(pk=instance.pk)
	except sender.DoesNotExist:
		pass


@receiver(post_save)
def audit_model_save(sender, instance, created, **kwargs):
	key = f"{getattr(sender, '_meta', None) and sender._meta.app_label}.{getattr(sender, '__name__', '')}"
	if key not in AUDIT_MODEL_ALLOWLIST:
		return
	
	changes = {}
	if not created:
		prev = _previous.pop((key, str(instance.pk)), None)
		if prev is not None:
			changes = model_diff(instance, prev)
	
	audit_log(
		action=f"model.{key}.{'created' if created else 'updated'}",
		obj=instance,
		changes=changes,
		metadata={"source": "signal"},
	)


@receiver(post_delete)
def audit_model_delete(sender, instance, **kwargs):
	key = f"{getattr(sender, '_meta', None) and sender._meta.app_label}.{getattr(sender, '__name__', '')}"
	if key not in AUDIT_MODEL_ALLOWLIST:
		return
	audit_log(action=f"model.{key}.deleted", obj=instance, metadata={"source": "signal"})