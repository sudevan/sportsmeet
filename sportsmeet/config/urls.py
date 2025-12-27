from django.urls import path, include

from accounts.admin_site import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("api/", include("meet.urls")),
    path("accounts/", include("accounts.urls")),
]
