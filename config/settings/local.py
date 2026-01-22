from .base import *

DEBUG = True


ALLOWED_HOSTS = [
	"localhost",
	"127.0.0.1",
	"admin.horstenhomes.local",
	".horstenhomes.local",
]

# Dev-friendly: print password reset links to console logs
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@horstenhomes.local"