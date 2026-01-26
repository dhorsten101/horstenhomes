from __future__ import annotations

from django import forms
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import User
from apps.contacts.models import Contact
from apps.core.forms import BootstrapModelForm


class TenantUserCreateForm(BootstrapModelForm):
	"""
	Create an employee user in the *tenant* schema.

	We do NOT set a password here; instead we create an unusable password and
	generate a one-time set-password link (like provisioning).
	"""

	email = forms.EmailField()
	first_name = forms.CharField(max_length=120)
	last_name = forms.CharField(max_length=120)
	is_staff = forms.BooleanField(
		required=False,
		help_text="Allow this user to manage employees (Users screen).",
	)

	class Meta:
		model = User
		fields = ["email", "is_staff", "is_active"]

	def save(self, *, request, commit: bool = True) -> tuple[User, str]:
		"""
		Returns (user, set_password_link).
		"""
		email = (self.cleaned_data.get("email") or "").strip().lower()
		first = (self.cleaned_data.get("first_name") or "").strip()
		last = (self.cleaned_data.get("last_name") or "").strip()
		display_name = (f"{first} {last}".strip() or email)
		is_staff = bool(self.cleaned_data.get("is_staff") or False)
		is_active = bool(self.cleaned_data.get("is_active") if "is_active" in self.cleaned_data else True)

		# Create via manager to trigger max_users quota enforcement.
		user = User.objects.create_user(email=email, password=None, is_staff=is_staff, is_active=is_active)

		# Create/attach contact so navbar can show initials/name.
		contact = Contact.objects.filter(email__iexact=email).first()
		if not contact:
			contact = Contact.objects.create(display_name=display_name, email=email)
		else:
			if (contact.display_name or "").strip() != display_name:
				contact.display_name = display_name
				contact.save(update_fields=["display_name", "updated_at"])
		user.contact = contact
		if commit:
			user.save()

		uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
		token = default_token_generator.make_token(user)
		path = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
		link = f"{request.scheme}://{request.get_host()}{path}"
		return user, link


class TenantUserUpdateForm(BootstrapModelForm):
	email = forms.EmailField(disabled=True, help_text="Email is the username and cannot be changed.")
	first_name = forms.CharField(max_length=120, required=False)
	last_name = forms.CharField(max_length=120, required=False)
	is_staff = forms.BooleanField(required=False)

	class Meta:
		model = User
		fields = ["email", "is_staff", "is_active"]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		u: User | None = getattr(self, "instance", None)
		if u and getattr(u, "pk", None) and getattr(u, "contact", None) and getattr(u.contact, "display_name", None):
			parts = [p for p in (u.contact.display_name or "").split(" ") if p]
			if parts:
				self.fields["first_name"].initial = parts[0]
				if len(parts) > 1:
					self.fields["last_name"].initial = " ".join(parts[1:])

	def save(self, commit=True):
		u: User = super().save(commit=commit)
		first = (self.cleaned_data.get("first_name") or "").strip()
		last = (self.cleaned_data.get("last_name") or "").strip()
		if first or last:
			display_name = f"{first} {last}".strip()
			contact = getattr(u, "contact", None)
			if contact is None:
				contact = Contact.objects.filter(email__iexact=u.email).first()
			if contact is None:
				contact = Contact.objects.create(display_name=display_name, email=u.email)
			else:
				contact.display_name = display_name
				contact.save(update_fields=["display_name", "updated_at"])
			if getattr(u, "contact_id", None) != contact.pk:
				u.contact = contact
				u.save(update_fields=["contact"])
		return u

