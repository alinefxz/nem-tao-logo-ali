from scripts.config import (
    BONUS_CHECKPOINT,
    BONUS_FASE,
    BONUS_SEM_MORTES,
    PENALIDADE_MORTE,
)


class GerenciadorPontuacao:
    def __init__(self):
        self.pontos = 0
        self.total_mortes = 0
        self.mortes_fase = 0

    def nova_fase(self):
        self.mortes_fase = 0

    @property
    def pontuacao(self):
        return self.pontos

    def registrar_morte(self):
        self.total_mortes += 1
        self.mortes_fase += 1
        self.pontos = max(0, self.pontos - PENALIDADE_MORTE)

    def checkpoint(self, ja_contado):
        if not ja_contado:
            self.pontos += BONUS_CHECKPOINT
        return not ja_contado

    def concluir_fase(self, bonus_tempo):
        bonus_tempo = max(0, min(200, int(bonus_tempo)))
        ganhos = BONUS_FASE + bonus_tempo
        if self.mortes_fase == 0:
            ganhos += BONUS_SEM_MORTES
        self.pontos += ganhos
        return ganhos
