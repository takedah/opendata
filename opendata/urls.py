from django.contrib import admin
from django.urls import include, path

from outpatients.views import top

urlpatterns = [
    path("", top, name="top"),
    path("admin/", admin.site.urls),
    path("outpatients/", include("outpatients.urls")),
    path("accounts/", include("accounts.urls")),
]
