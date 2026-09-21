"""Compatibilidade mínima para protótipos antigos do projeto.

O jogo atual usa ``scripts.pontuacao`` e ``scripts.obstaculos``. Estas duas
classes permanecem disponíveis para exemplos antigos sem conter lógica
paralela ou referências inválidas.
"""

import pygame


class GerenciadorPontuacao:
    def __init__(self):
        self.pontuacao = 0

    def concluir_fase(self, mortes_na_fase=0):
        self.pontuacao += 300
        if mortes_na_fase == 0:
            self.pontuacao += 150
        return self.pontuacao

    def registrar_morte(self):
        self.pontuacao = max(0, self.pontuacao - 25)


class ObstaculoFixo:
    def __init__(self, tela, x, y, largura, altura):
        self.tela = tela
        self.rect = pygame.Rect(x, y, largura, altura)

    def desenhar(self, tela=None):
        pygame.draw.rect(tela or self.tela, (0, 0, 0), self.rect)

    def detectarColisao(self, rect_jogador):
        return rect_jogador.colliderect(self.rect)
