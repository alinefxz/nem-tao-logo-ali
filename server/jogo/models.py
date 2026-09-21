from django.db import models


class Jogador(models.Model):
    nome = models.CharField(max_length=20, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Resultado(models.Model):
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name="resultados")
    pontuacao = models.PositiveIntegerField(default=0)
    mortes = models.PositiveIntegerField(default=0)
    tempo = models.FloatField(default=0.0)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pontuacao", "mortes", "tempo", "data")

    def __str__(self):
        return f"{self.jogador.nome} - {self.pontuacao} pts"