from django.contrib.auth.base_user import BaseUserManager
from django.db import connection


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra):
		if not email:
			raise ValueError("Email is required")

		# Enforce per-tenant max users (counts tenant-schema users only).
		schema = getattr(connection, "schema_name", "") or ""
		if schema and schema != "public":
			try:
				from apps.entitlements.services import QUOTA_MAX_USERS, enforce_quota, get_tenant_by_schema

				tenant_row = get_tenant_by_schema(schema)
				if tenant_row:
					used = self.model.objects.count()
					enforce_quota(
						tenant_row,
						key=QUOTA_MAX_USERS,
						used=used,
						needed=1,
						action="quota.max_users.exceeded",
						obj=None,
						metadata={"model": "accounts.User"},
					)
			except Exception:
				# Soft mode or misconfiguration should never break user creation unexpectedly.
				# Hard mode enforcement raises ValidationError before we reach here.
				pass

		email = self.normalize_email(email)
		user = self.model(email=email, **extra)
		user.set_password(password)
		user.save(using=self._db)
		return user
	
	def create_superuser(self, email, password=None, **extra):
		extra.setdefault("is_staff", True)
		extra.setdefault("is_superuser", True)
		return self.create_user(email, password, **extra)