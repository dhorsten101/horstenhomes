from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Public marketing site (public schema)
    path("", include("apps.marketing.urls")),
    
    # Public onboarding (public schema)
    path("", include("apps.onboarding.urls")),
    
    # Tenant UI (tenant schema)
    path("", include("apps.web.urls")),
    
    path("", include("apps.audits.urls")),
    
    # Admin (public schema on admin.*; tenant schema on tenant hostnames)
    path("admin/", admin.site.urls),
    
]