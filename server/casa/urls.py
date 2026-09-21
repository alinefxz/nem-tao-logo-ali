from django.contrib import admin
from django.urls import include, path

from jogo.views import inicio

urlpatterns = [
    path("", inicio, name="inicio"),
    path("admin/", admin.site.urls),
    path("api/", include("jogo.urls")),
]