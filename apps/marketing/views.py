from django.shortcuts import render

def landing_view(request):
	return render(request, "marketing/landing.html")

def pricing_view(request):
	return render(request, "marketing/pricing.html")