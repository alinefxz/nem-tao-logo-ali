from django.urls import path

from . import views

urlpatterns = [
    path("resultados/", views.resultados),
    path("ranking/", views.ranking),
]