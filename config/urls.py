from django.urls import path, include

from accounts.admin_site import admin_site
from accounts.urls import admin_dashboard

urlpatterns = [
    path("admin/", admin_dashboard),
    path("django-admin/", admin_site.urls),
    path("api/", include("meet.urls")),
    path("accounts/", include("accounts.urls")),
]
