from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User


class UserCreationForm(forms.ModelForm):
	password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
	password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

	class Meta:
		model = User
		fields = ("email",)

	def clean_password2(self):
		p1 = self.cleaned_data.get("password1")
		p2 = self.cleaned_data.get("password2")
		if p1 and p2 and p1 != p2:
			raise forms.ValidationError("Passwords don't match.")
		return p2

	def save(self, commit=True):
		user: User = super().save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
		return user


class UserChangeForm(forms.ModelForm):
	password = ReadOnlyPasswordHashField(
		label="Password",
		help_text=_(
			"Raw passwords are not stored, so there is no way to see this user's password, "
			"but you can change the password using <a href=\"../password/\">this form</a>."
		),
	)

	class Meta:
		model = User
		fields = (
			"email",
			"password",
			"is_active",
			"is_staff",
			"is_superuser",
			"groups",
			"user_permissions",
			"contact",
			"tags",
		)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	form = UserChangeForm
	add_form = UserCreationForm

	list_display = ("email", "is_staff", "is_active", "date_joined", "updated_at")
	list_filter = ("is_staff", "is_active", "is_superuser", "groups")
	search_fields = ("email",)
	ordering = ("email",)

	fieldsets = (
		(None, {"fields": ("email", "password")}),
		(_("Profile"), {"fields": ("contact", "tags")}),
		(
			_("Permissions"),
			{"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
		),
		(_("Important dates"), {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
	)

	add_fieldsets = (
		(None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_staff", "is_active")}),
	)

	readonly_fields = ("created_at", "updated_at")
	filter_horizontal = ("groups", "user_permissions")
