import os
from pathlib import Path

from dotenv import load_dotenv

# -------------------------------------------------
# Paths / env
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

# Load env vars (works in Docker + PyCharm)
load_dotenv(BASE_DIR / ".env.dev")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DEBUG", "0") in ("1", "true", "True")

ALLOWED_HOSTS = [
	h.strip()
	for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
	if h.strip()
]

# -------------------------------------------------
# Applications
# -------------------------------------------------

SHARED_APPS = (
	"django_tenants",

	# Django internals needed on the public schema
	"django.contrib.contenttypes",
	"django.contrib.messages",
	"django.contrib.staticfiles",

	# Optional: only if you want `/admin/` on public schema
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.sessions",

	# Cross-cutting (shared)
	"apps.audits.apps.AuditsConfig",
	"apps.logs.apps.LogsConfig",
	"apps.activity.apps.ActivityConfig",
	"apps.entitlements.apps.EntitlementsConfig",
	
	# Shared data models required by AUTH_USER_MODEL and admin on public schema
	"apps.core",
	"apps.addresses",
	"apps.contacts",
	"apps.accounts",

	# Public control-plane apps (only these should live in public)
	"apps.tenancy",  # Tenant + Domain
	"apps.onboarding",  # TenantRequest intake
	"apps.marketing",  # pricing/landing pages

	# Platform UI (public schema only; views enforce this)
	"apps.platform",
)

TENANT_APPS = (
	# Standard Django tenant apps
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",

	# Cross-cutting
	"apps.audits.apps.AuditsConfig",
	"apps.logs.apps.LogsConfig",
	"apps.activity.apps.ActivityConfig",

	# Tenant business/domain apps
	"apps.core",
	"apps.accounts",
	"apps.addresses",
	"apps.contacts",
	"apps.portfolio",
	"apps.properties",
	"apps.leases",
	"apps.documents",
	"apps.todo",
	"apps.branding",
	"apps.web",
)



INSTALLED_APPS = list(SHARED_APPS) + [
	app for app in TENANT_APPS if app not in SHARED_APPS
]

# -------------------------------------------------
# Database (PostgreSQL + django-tenants)
# -------------------------------------------------
DATABASES = {
	"default": {
		"ENGINE": "django_tenants.postgresql_backend",
		"NAME": os.environ.get("DB_NAME", "horstenhomes"),
		"USER": os.environ.get("DB_USER", "horstenhomes"),
		"PASSWORD": os.environ.get("DB_PASSWORD", "horstenhomes"),
		"HOST": os.environ.get("DB_HOST", "hh-postgres"),
		"PORT": os.environ.get("DB_PORT", "5432"),
	}
}

DATABASE_ROUTERS = (
	"django_tenants.routers.TenantSyncRouter",
)

TENANT_MODEL = "tenancy.Tenant"
TENANT_DOMAIN_MODEL = "tenancy.Domain"
PUBLIC_SCHEMA_NAME = "public"


# -------------------------------------------------
# Auth (tenant-local users)
# -------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/accounts/profile/"
LOGOUT_REDIRECT_URL = "/login/"

# -------------------------------------------------
# Sentry (optional)
# -------------------------------------------------
SENTRY_DSN = os.environ.get("SENTRY_DSN", "").strip()
if SENTRY_DSN:
	try:
		import sentry_sdk
		from sentry_sdk.integrations.django import DjangoIntegration
		from sentry_sdk.integrations.logging import LoggingIntegration

		# - breadcrumbs: keep lightweight context (INFO+)
		# - events: forward errors (ERROR+)
		sentry_logging = LoggingIntegration(level="INFO", event_level="ERROR")

		sentry_sdk.init(
			dsn=SENTRY_DSN,
			integrations=[DjangoIntegration(), sentry_logging],
			environment=os.environ.get("SENTRY_ENVIRONMENT", "local"),
			send_default_pii=False,
			# Start low; tune per environment.
			traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
		)
	except Exception:
		# Never block app startup because of Sentry.
		pass

# -------------------------------------------------
# Middleware (ORDER MATTERS)
# -------------------------------------------------
MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	
	# MUST be before auth/session middleware
	"django_tenants.middleware.main.TenantMainMiddleware",
	"apps.audits.middleware.AuditContextMiddleware",
	
	
	"apps.tenancy.middleware.TenantStatusMiddleware",
	"apps.entitlements.middleware.ApiQuotaMiddleware",
	
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	# Guard Django admin access (public superuser-only; disabled on tenant schemas)
	"apps.core.middleware.AdminPortalGuardMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
	# Performance + DB slow query alerts
	"apps.logs.middleware.PerformanceAlertMiddleware",
	# Persist unhandled exceptions as alerts
	"apps.logs.middleware.ExceptionAlertMiddleware",
]

# -------------------------------------------------
# Entitlements / quotas (soft -> hard enforcement)
# -------------------------------------------------
# - "soft": allow but log/audit quota violations
# - "hard": raise ValidationError on violations (blocking writes)
ENTITLEMENTS_ENFORCEMENT = os.environ.get("ENTITLEMENTS_ENFORCEMENT", "soft").strip().lower()

# -------------------------------------------------
# Celery (async jobs)
# -------------------------------------------------
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://hh-redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://hh-redis:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "0") in ("1", "true", "True")

CELERY_BEAT_SCHEDULE = {
	"audit.purge.daily": {
		"task": "apps.logs.tasks.purge_audit_events_task",
		"schedule": 60 * 60 * 24,
		"args": (90,),
	},
}

# -------------------------------------------------
# URLs / WSGI
# -------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# -------------------------------------------------
# Templates
# -------------------------------------------------
TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [BASE_DIR / "templates"],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
				"apps.branding.context_processors.tenant_branding",
			],
		},
	},
]

# -------------------------------------------------
# Internationalization
# -------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------
# Static files
# -------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# -------------------------------------------------
# Media uploads (Documents, etc.)
# -------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------
# Reverse proxy safety (prod-safe, harmless in dev)
# -------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# -------------------------------------------------
# Logging
# -------------------------------------------------
LOGGING = {
	"version": 1,
	"disable_existing_loggers": False,
	"handlers": {
		"db": {
			"level": "INFO",
			"class": "apps.logs.handlers.DatabaseLogHandler",
		},
	},
	"root": {
		"handlers": ["db"],
		"level": "INFO",
	},
	"loggers": {
		# allow fine-grained level control without flooding logs
		"db.query": {"level": "WARNING"},
		"web.request": {"level": "WARNING"},
	},
}

# -------------------------------------------------
# Alert thresholds (ms)
# -------------------------------------------------
SLOW_REQUEST_MS = int(os.environ.get("SLOW_REQUEST_MS", "1000"))
SLOW_DB_QUERY_MS = int(os.environ.get("SLOW_DB_QUERY_MS", "200"))

