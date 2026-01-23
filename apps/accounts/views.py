from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@login_required
def profile_view(request):
	return render(request, "accounts/profile.html")


class DevPasswordResetView(PasswordResetView):
	"""
	Dev/testing convenience: after submitting the reset form, expose the
	password-reset link on the "done" page so you don't need email configured.
	"""

	SESSION_KEY = "dev_password_reset_link"

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
