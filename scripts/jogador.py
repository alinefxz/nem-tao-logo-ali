import pygame

from scripts.animacao import Animacao
from scripts.assets import carregar_animacao
from scripts.config import (
    ALTURA_JOGADOR,
    CHAO_Y,
    GRAVIDADE,
    LARGURA_JOGADOR,
    VEL_CORRIDA,
    VEL_DERRAPAGEM,
    VEL_PULO,
)


class Jogador:
    def __init__(self, x, y, altura=ALTURA_JOGADOR):
        self.x = float(x)
        self.y = float(y)
        self.chao_y = float(CHAO_Y)
        self.altura = altura
        self.largura = LARGURA_JOGADOR
        self.vx = 0.0
        self.vy = 0.0
        self.no_chao = True
        self.morto = False
        self.motivo_morte = ""
        self.estado = "parada"
        self.tempo_estado = 0.0
        self.animacoes = {}
        self._carregar_animacoes()
        self.rect = self._criar_rect()
        self._atualizar_rect()

    def _carregar_animacoes(self):
        configuracoes = {
            "parada": (5, True),
            "correr": (10, True),
            "pular": (8, False),
            "cair": (8, False),
            "aterrissando": (10, False),
            "morrendo": (8, False),
            "respawn": (8, False),
            "derrapando": (10, False),
        }
        for estado, (fps, loop) in configuracoes.items():
            self.animacoes[estado] = Animacao(carregar_animacao("personagem", estado, self.altura), fps, loop)

    def _criar_rect(self):
        return pygame.Rect(0, 0, self.largura, self.altura)

    def _atualizar_rect(self):
        self.rect.midbottom = (round(self.x), round(self.y))

    def mover(self, direcao):
        if self.morto:
            return
        direcao = max(-1, min(1, int(direcao)))
        self.vx = direcao * VEL_CORRIDA
        if not self.no_chao:
            return
        if direcao == 0:
            self.definir_estado("parada")
        else:
            self.definir_estado("correr")

    def pular(self):
        if not self.morto and self.no_chao:
            self.vy = VEL_PULO
            self.no_chao = False
            self.definir_estado("pular")

    def derrapar(self):
        if not self.morto:
            self.vx = VEL_DERRAPAGEM if self.vx >= 0 else -VEL_DERRAPAGEM
            self.definir_estado("derrapando")

    def atualizar(self, dt, solidos=None, plataformas=None):
        if self.morto:
            self.animacoes[self.estado].atualizar(dt)
            self._atualizar_rect()
            return

        solidos = list(solidos or []) + list(plataformas or [])
        self.x += self.vx * dt
        rect_anterior = self.rect.copy()
        self.vy += GRAVIDADE * dt
        self.y += self.vy * dt
        self.no_chao = False

        if self.vy >= 0:
            for solido in solidos:
                if rect_anterior.bottom <= solido.top and self._horizontalmente_sobre(solido):
                    if self.y >= solido.top:
                        self.y = solido.top
                        self.vy = 0.0
                        self.no_chao = True
                        break
        if not self.no_chao and self.y >= self.chao_y:
            self.y = self.chao_y
            self.vy = 0.0
            self.no_chao = True

        if not self.no_chao:
            self.definir_estado("pular" if self.vy < 0 else "cair")
        elif abs(self.vx) < 1:
            self.definir_estado("parada")
        elif self.estado not in ("derrapando", "aterrissando"):
            self.definir_estado("correr")

        self.tempo_estado += dt
        self.animacoes[self.estado].atualizar(dt)
        self._atualizar_rect()

    def _horizontalmente_sobre(self, solido):
        return self.rect.right > solido.left and self.rect.left < solido.right

    def definir_estado(self, estado):
        if estado not in self.animacoes:
            estado = "parada"
        if estado != self.estado:
            self.estado = estado
            self.tempo_estado = 0.0
            self.animacoes[estado].reiniciar()

    def morrer(self, motivo="morte"):
        if not self.morto:
            self.morto = True
            self.motivo_morte = motivo
            self.vx = 0.0
            self.vy = 0.0
            self.definir_estado("morrendo")

    def reiniciar(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.no_chao = True
        self.morto = False
        self.motivo_morte = ""
        self.definir_estado("parada")
        self._atualizar_rect()

    def morreu_no_buraco(self, hitboxes):
        return self.no_chao and any(self.rect.colliderect(hitbox) for hitbox in hitboxes)

    def getRect(self):
        return self.rect.copy()

    def desenhar(self, tela, camera_x=0, alpha=255):
        imagem = self.animacoes[self.estado].imagem()
        if alpha != 255:
            imagem = imagem.copy()
            imagem.set_alpha(alpha)
        destino = imagem.get_rect(midbottom=(round(self.x - camera_x), round(self.y)))
        tela.blit(imagem, destino)
