from django.urls import path, include
from accounts.admin_site import admin_site
from django.shortcuts import redirect

def admin_redirect(request):
    return redirect("accounts:admin_dashboard")

urlpatterns = [
    path("admin/", admin_redirect),
    path("django-admin/", admin_site.urls),
    path("api/", include("meet.urls")),
    path("", include("accounts.urls")),
]