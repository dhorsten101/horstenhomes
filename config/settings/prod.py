from .base import *

# Production
DEBUG = False

# In prod you should set ALLOWED_HOSTS via env (base.py already reads it).
# Do not override it here unless you have a fixed host list.

# -------------------------------------------------
# Django security flags (prod)
# -------------------------------------------------
# HTTPS / proxy
SECURE_SSL_REDIRECT = True

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True

# HSTS
# Start with 1 hour; increase (e.g. 31536000) after validating TLS + redirects.
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1") in ("1", "true", "True")
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "0") in ("1", "true", "True")

# Browser hardening
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = os.environ.get("X_FRAME_OPTIONS", "DENY")
SECURE_REFERRER_POLICY = os.environ.get("SECURE_REFERRER_POLICY", "same-origin")

# CSRF trusted origins (needed for subdomains / reverse proxy)
_csrf_env = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_env:
	CSRF_TRUSTED_ORIGINS = [x.strip() for x in _csrf_env.split(",") if x.strip()]
else:
	_base_domain = os.environ.get("BASE_TENANT_DOMAIN", "").strip()
	if _base_domain:
		CSRF_TRUSTED_ORIGINS = [f"https://*.{_base_domain}"]