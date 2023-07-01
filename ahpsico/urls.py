from django.contrib import admin
from django.urls import include, path, re_path

from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title="Pastebin API")

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^$", schema_view),
    path("", include("api.urls")),
]
