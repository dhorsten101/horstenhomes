from pathlib import Path
import os
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
	"django.contrib.contenttypes",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	
	# Public (control-plane) schema
	"apps.tenancy",
)

TENANT_APPS = (
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	
	# Tenant-local apps
	"apps.accounts",
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

# -------------------------------------------------
# Middleware (ORDER MATTERS)
# -------------------------------------------------
MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	
	# MUST be before auth/session middleware
	"django_tenants.middleware.main.TenantMainMiddleware",
	
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------
# Reverse proxy safety (prod-safe, harmless in dev)
# -------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True