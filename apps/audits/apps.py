from django.apps import AppConfig


class AuditsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audits"
    verbose_name = "Audit Logs"
    
    def ready(self):
        # Import signal modules ONLY when Django app registry is ready.
        from . import auth_signals  # noqa: F401
        from . import model_audit   # noqa: F401