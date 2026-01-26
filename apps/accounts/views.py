from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetView, redirect_to_login
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import ListView, UpdateView

from apps.accounts.forms import TenantUserCreateForm, TenantUserUpdateForm
from apps.accounts.models import User
from apps.audits.services import audit_log
from apps.core.mixins import TenantSchemaRequiredMixin
from apps.tenancy.models import Domain, Tenant


@login_required
def profile_view(request):
	return render(request, "accounts/profile.html")


class TenantAdminRequiredMixin(TenantSchemaRequiredMixin, LoginRequiredMixin, UserPassesTestMixin):
	"""
	Tenant staff-only screens (employee user management).
	"""

	def test_func(self):
		return bool(getattr(self.request.user, "is_staff", False))


class TenantUserListView(TenantAdminRequiredMixin, ListView):
	model = User
	template_name = "accounts/user_list.html"
	context_object_name = "users"
	paginate_by = 50

	def get_queryset(self):
		qs = User.objects.all().order_by("email")
		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(Q(email__icontains=q))
		return qs

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


def _set_password_link_for_user(request, user: User) -> str:
	uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
	token = default_token_generator.make_token(user)
	path = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
	return f"{request.scheme}://{request.get_host()}{path}"


def tenant_user_create_view(request):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		return redirect("landing")
	if not request.user.is_authenticated:
		return redirect_to_login(request.get_full_path())
	if not getattr(request.user, "is_staff", False):
		return redirect("crm_dashboard")

	if request.method == "POST":
		form = TenantUserCreateForm(request.POST)
		if form.is_valid():
			u, link = form.save(request=request)
			audit_log(action="accounts.user.created", obj=u, metadata={"email": u.email})
			messages.success(request, f"Created user: {u.email}")
			messages.warning(request, f"Set-password link for {u.email}: {link}")
			return redirect("accounts:user_list")
	else:
		form = TenantUserCreateForm(initial={"is_active": True})

	return render(
		request,
		"accounts/user_form.html",
		{
			"title": "Create user",
			"form": form,
			"back_url": reverse("accounts:user_list"),
			"cancel_url": reverse("accounts:user_list"),
			"submit_text": "Create user",
		},
	)


class TenantUserUpdateView(TenantAdminRequiredMixin, UpdateView):
	model = User
	form_class = TenantUserUpdateForm
	template_name = "accounts/user_form.html"

	def form_valid(self, form):
		# Ensure contact display name is updated (form has non-model fields).
		self.object = form.save()
		resp = redirect(self.get_success_url())
		audit_log(action="accounts.user.updated", obj=self.object, metadata={"email": self.object.email})
		messages.success(self.request, f"Updated user: {self.object.email}")
		return resp

	def get_success_url(self):
		return reverse("accounts:user_list")

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx.update(
			{
				"title": f"Edit user: {self.object.email}",
				"back_url": reverse("accounts:user_list"),
				"cancel_url": reverse("accounts:user_list"),
				"submit_text": "Save",
			}
		)
		return ctx


def tenant_user_set_password_link_view(request, pk: int):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		return redirect("landing")
	if not request.user.is_authenticated:
		return redirect_to_login(request.get_full_path())
	if not getattr(request.user, "is_staff", False):
		return redirect("crm_dashboard")
	if request.method != "POST":
		return redirect("accounts:user_list")

	u = User.objects.filter(pk=pk).first()
	if not u:
		messages.error(request, "User not found.")
		return redirect("accounts:user_list")

	link = _set_password_link_for_user(request, u)
	audit_log(action="accounts.user.set_password_link", obj=u, metadata={"email": u.email})
	messages.warning(request, f"Set-password link for {u.email}: {link}")
	return redirect("accounts:user_list")


def tenant_user_toggle_active_view(request, pk: int):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		return redirect("landing")
	if not request.user.is_authenticated:
		return redirect_to_login(request.get_full_path())
	if not getattr(request.user, "is_staff", False):
		return redirect("crm_dashboard")
	if request.method != "POST":
		return redirect("accounts:user_list")

	u = User.objects.filter(pk=pk).first()
	if not u:
		messages.error(request, "User not found.")
		return redirect("accounts:user_list")

	u.is_active = not bool(u.is_active)
	u.save(update_fields=["is_active", "updated_at"])
	audit_log(action="accounts.user.toggled_active", obj=u, metadata={"email": u.email, "is_active": u.is_active})
	messages.success(request, f"{'Activated' if u.is_active else 'Deactivated'} user: {u.email}")
	return redirect("accounts:user_list")

def tenant_aware_login_view(request):
	"""
	Login behavior depends on host/schema:

	- Public host (schema=public): show a "tenant locator" (enter slug/domain) and
	  redirect to the correct tenant `/login/`.
	- Tenant host: show the normal Django LoginView (email + password).
	"""
	tenant = getattr(request, "tenant", None)
	if tenant and getattr(tenant, "schema_name", None) != "public":
		return auth_views.LoginView.as_view(template_name="auth/login.html")(request)

	error = ""
	next_url = (request.GET.get("next") or "").strip()
	email_prefill = (request.GET.get("email") or "").strip()

	if request.method == "POST":
		raw = (request.POST.get("tenant") or "").strip().lower()
		next_url = (request.POST.get("next") or next_url).strip()
		flow = (request.POST.get("flow") or "login").strip().lower()
		email_prefill = (request.POST.get("email") or email_prefill).strip()

		host = None
		if not raw:
			error = "Enter your tenant slug (e.g. company2) or domain."
		else:
			# Allow either:
			# - slug: "company2"
			# - domain: "company2.horstenhomes.local" (with or without port)
			if "." in raw:
				host = raw
			else:
				t = Tenant.objects.filter(slug=raw).first() or Tenant.objects.filter(schema_name=raw).first()
				if not t or getattr(t, "schema_name", "") == "public":
					error = "Tenant not found. Check the slug and try again."
					t = None
				if t:
					d = Domain.objects.filter(tenant=t, is_primary=True).first()
					host = (d.domain if d else f"{t.slug}.{getattr(settings, 'BASE_TENANT_DOMAIN', 'horstenhomes.local')}")

			# Ensure dev port is preserved if your tenant domain doesn't include a port.
			if host and not error and ":" not in host:
				port = (request.get_port() or "").strip()
				if port and port not in {"80", "443"}:
					host = f"{host}:{port}"

			if host and not error:
				scheme = request.scheme or "http"
				target_path = "/password-reset/" if flow in {"reset", "password_reset", "set_password"} else "/login/"
				target = f"{scheme}://{host}{target_path}"

				from urllib.parse import urlencode

				qs = {}
				if next_url and target_path == "/login/":
					qs["next"] = next_url
				if email_prefill and target_path == "/password-reset/":
					qs["email"] = email_prefill
				if qs:
					target = f"{target}?{urlencode(qs)}"
				return redirect(target)

	return render(request, "auth/tenant_login.html", {"error": error, "next": next_url, "email": email_prefill})


class DevPasswordResetView(PasswordResetView):
	"""
	Dev/testing convenience: after submitting the reset form, expose the
	password-reset link on the "done" page so you don't need email configured.
	"""

	SESSION_KEY = "dev_password_reset_link"

	def get_initial(self):
		initial = super().get_initial()
		email = (self.request.GET.get("email") or "").strip()
		if email:
			initial["email"] = email
		return initial

	def form_valid(self, form):
		response = super().form_valid(form)

		# Only do this in DEBUG to avoid leaking reset links in production.
		if settings.DEBUG:
			email = (form.cleaned_data.get("email") or "").strip().lower()
			User = get_user_model()

			# Mirror PasswordResetForm behavior: only for active users with usable password.
			user = (
				User.objects.filter(email__iexact=email, is_active=True)
				.exclude(password="")
				.first()
			)

			if user:
				uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
				token = default_token_generator.make_token(user)
				path = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
				link = f"{self.request.scheme}://{self.request.get_host()}{path}"
				self.request.session[self.SESSION_KEY] = link
			else:
				self.request.session.pop(self.SESSION_KEY, None)

		return response


class DevPasswordResetDoneView(PasswordResetDoneView):
	SESSION_KEY = DevPasswordResetView.SESSION_KEY

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		# Keep link available for refresh/copy during testing.
		ctx["dev_reset_link"] = self.request.session.get(self.SESSION_KEY)
		ctx["debug"] = settings.DEBUG
		return ctx
