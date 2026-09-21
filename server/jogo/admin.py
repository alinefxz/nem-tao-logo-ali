from django.contrib import admin

from .models import Jogador, Resultado


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    list_display = ("nome", "criado_em")
    search_fields = ("nome",)


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ("jogador", "pontuacao", "mortes", "tempo", "data")
    list_filter = ("data",)
    search_fields = ("jogador__nome",)