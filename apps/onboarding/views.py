from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import TenantRequest


def signup_view(request):
	if request.method == "POST":
		TenantRequest.objects.create(
			company_name=request.POST.get("company_name", "").strip(),
			desired_slug=request.POST.get("desired_slug", "").strip().lower(),
			contact_name=request.POST.get("contact_name", "").strip(),
			contact_email=request.POST.get("contact_email", "").strip().lower(),
			contact_phone=request.POST.get("contact_phone", "").strip(),
		)
		return HttpResponseRedirect(reverse("tenant_signup_done"))
	
	return render(request, "onboarding/signup.html")


def signup_done_view(request):
	return render(request, "onboarding/signup_done.html")