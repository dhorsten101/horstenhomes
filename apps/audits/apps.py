from django.apps import AppConfig


class AuditsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audits"
    verbose_name = "Audit Logs"
    
    def ready(self):
        # Import signal modules ONLY when Django app registry is ready.
        # Production-grade default: audit CRUD across the whole project.
        # We auto-register all models in the local "apps.*" namespace, excluding:
        # - AuditEvent itself (avoid recursion)
        # - auto-created / proxy models (noise)
        from django.apps import apps as django_apps

        from apps.audits.model_audit import register_model
        from apps.audits.models import AuditEvent

        from . import (
            auth_signals,  # noqa: F401
            model_audit,  # noqa: F401
        )

        for model in django_apps.get_models():
            if model is AuditEvent:
                continue
            if model._meta.auto_created or model._meta.proxy:
                continue
            if not (getattr(model, "__module__", "") or "").startswith("apps."):
                continue
            register_model(model)