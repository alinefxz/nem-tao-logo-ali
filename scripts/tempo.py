from scripts.config import BONUS_TEMPO_MAX, TEMPO_REFERENCIA


class GerenciadorTempo:
    def __init__(self):
        self.tempos_fase = [0.0] * len(TEMPO_REFERENCIA)
        self.fase_atual = -1
        self.atual = 0.0
        self.pausado = False

    def iniciar_fase(self, indice):
        if indice < 0 or indice >= len(self.tempos_fase):
            raise ValueError(f"índice de fase inválido: {indice}")
        self.fase_atual = indice
        self.atual = 0.0
        self.pausado = False

    def acumular(self, dt):
        if not self.pausado:
            self.atual += dt

    def tempo_fase(self):
        return self.atual

    def tempo_total(self):
        total = sum(self.tempos_fase)
        if self.fase_atual >= 0 and self.tempos_fase[self.fase_atual] == 0:
            total += self.atual
        return total

    def concluir_fase(self):
        if self.fase_atual >= 0:
            self.tempos_fase[self.fase_atual] = self.atual

    def bonus_fase(self, indice):
        if indice < 0 or indice >= len(TEMPO_REFERENCIA):
            return 0
        ref = TEMPO_REFERENCIA[indice]
        usado = self.tempos_fase[indice] if indice < self.fase_atual or self.fase_atual != indice else self.atual
        if usado >= ref:
            return 0
        bonus = int(BONUS_TEMPO_MAX * (ref - usado) / ref)
        return max(0, min(BONUS_TEMPO_MAX, bonus))
