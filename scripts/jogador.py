import pygame

from scripts.animacao import Animacao
from scripts.assets import altura_referencia_animacao, carregar_animacao
from scripts.config import (
    ALTURA_JOGADOR,
    LARGURA_BUEIRO,
    CHAO_Y,
    GRAVIDADE,
    LARGURA_JOGADOR,
    VEL_ANDAR,
    VEL_CORRIDA,
    VEL_DERRAPAGEM,
    VEL_PULO,
    TEMPO_RESPAWN,
)

LARGURA_BUEIRO_ANIMACAO_MIN = 76
LARGURA_BUEIRO_ANIMACAO_MAX = LARGURA_BUEIRO
FOLGA_BUEIRO_ANIMACAO = 8


class Jogador:
    """Personagem com física simples e estados visuais separados.

    ``y`` representa a base dos pés. Assim, todos os frames são desenhados
    pela mesma âncora, mesmo quando a pose muda de tamanho.
    """

    ESTADOS_TEMPORARIOS = {"aterrissando", "derrapando", "respawn"}

    def __init__(self, x, y, altura=ALTURA_JOGADOR):
        self.x = float(x)
        self.y = float(y)
        self.chao_y = float(CHAO_Y)
        self.suporte_y = float(y)
        self.suporte_plataforma = None
        self.altura = altura
        self.largura = LARGURA_JOGADOR
        self.vx = 0.0
        self.vy = 0.0
        self.correndo = False
        self.no_chao = True
        self.salto_ativo = False
        self.caindo_no_buraco = False
        self.morto = False
        self.motivo_morte = ""
        self.estado = "parada"
        self.tempo_estado = 0.0
        self._quadros_buraco_base = None
        self.animacoes = {}
        self._carregar_animacoes()
        self.rect = self._criar_rect()
        self._atualizar_rect()

    def _carregar_animacoes(self):
        configuracoes = {
            "parada": (6, True),
            "andar": (10, True),
            "correr": (12, True),
            "pular": (10, False),
            "cair": (10, False),
            "aterrissando": (12, False),
            "buraco": (12, False),
            "abaixar": (10, False),
            "derrapando": (12, False),
            "agua": (10, False),
            "morrendo": (10, False),
            # A sequência tem poucos quadros; a velocidade reduzida deixa o
            # retorno visível, enquanto o tempo mínimo abaixo mantém a
            # personagem protegida mesmo depois do último quadro.
            "respawn": (5, False),
        }
        altura_base = altura_referencia_animacao("personagem", "parada")
        for estado, (fps, loop) in configuracoes.items():
            if estado == "buraco":
                quadros = carregar_animacao(
                    "personagem",
                    estado,
                    self.altura,
                    altura_referencia=altura_base,
                )
                self._quadros_buraco_base = list(quadros)
            else:
                quadros = carregar_animacao("personagem", estado, self.altura)
            self.animacoes[estado] = Animacao(quadros, fps, loop)

    def _criar_rect(self):
        return pygame.Rect(0, 0, self.largura, self.altura)

    def _atualizar_rect(self):
        self.rect.midbottom = (round(self.x), round(self.y))

    def _animacao_temporaria_ativa(self):
        return (
            self.estado in self.ESTADOS_TEMPORARIOS
            and not self._animacao_temporaria_concluida()
        )

    def _animacao_temporaria_concluida(self):
        if self.estado == "respawn":
            return self.tempo_estado >= TEMPO_RESPAWN
        return self.animacoes[self.estado].concluida()

    def _respawn_bloqueando_entrada(self):
        return self.estado == "respawn" and not self._animacao_temporaria_concluida()

    def mover(self, direcao, correndo=False):
        if self.morto or self.caindo_no_buraco:
            self.correndo = False
            return
        if self._respawn_bloqueando_entrada():
            self.vx = 0.0
            self.correndo = False
            return
        direcao = max(-1, min(1, int(direcao)))
        self.correndo = correndo and direcao != 0
        velocidade = VEL_CORRIDA if correndo else VEL_ANDAR
        self.vx = direcao * velocidade
        if not self.no_chao:
            return
        if self._animacao_temporaria_ativa():
            return
        if direcao == 0:
            self.definir_estado("parada")
        else:
            self.definir_estado("correr" if correndo else "andar")

    def pular(self):
        if (
            not self.morto
            and self.no_chao
            and not self.caindo_no_buraco
            and not self._respawn_bloqueando_entrada()
        ):
            self.vy = VEL_PULO
            self.no_chao = False
            self.salto_ativo = True
            self.suporte_plataforma = None
            self.definir_estado("pular")

    def abaixar(self, ativo=True):
        if ativo and not self.morto and self.no_chao and not self._animacao_temporaria_ativa():
            self.vx = 0.0
            self.correndo = False
            self.definir_estado("abaixar")

    def derrapar(self):
        if not self.morto and self.no_chao and not self._respawn_bloqueando_entrada():
            self.vx = VEL_DERRAPAGEM if self.vx >= 0 else -VEL_DERRAPAGEM
            self.definir_estado("derrapando")

    def atualizar(self, dt, solidos=None, plataformas=None):
        if self.morto:
            self.animacoes[self.estado].atualizar(dt)
            self._atualizar_rect()
            return

        if self.caindo_no_buraco:
            # A própria sequência ``buraco`` contém a personagem entrando no
            # bueiro e também o piso/abertura. Não somamos gravidade aqui,
            # pois isso faria o sprite sair da tela antes de terminar os sete
            # quadros da animação.
            self.y = self.chao_y
            self.vy = 0.0
            self.no_chao = False
            self.definir_estado("buraco")
            self.tempo_estado += dt
            self.animacoes[self.estado].atualizar(dt)
            self._atualizar_rect()
            return

        solidos = list(solidos or []) + list(plataformas or [])
        if self._respawn_bloqueando_entrada():
            self.vx = 0.0
        self.x += self.vx * dt
        estava_no_chao = self.no_chao
        pousou = False

        if estava_no_chao:
            # Um personagem parado não deve ser tratado como se tivesse
            # pousado em todos os frames. Isso mantinha a animação de
            # aterrissagem presa e impedia a animação de parada.
            if self.suporte_y < self.chao_y and not self._tem_suporte(solidos):
                self.no_chao = False
                self.suporte_plataforma = None
            else:
                self.y = self.suporte_y
                self.vy = 0.0
        else:
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
                            self.suporte_y = float(solido.top)
                            self.suporte_plataforma = solido
                            pousou = True
                            break
            if not self.no_chao and self.y >= self.chao_y:
                self.y = self.chao_y
                self.vy = 0.0
                self.no_chao = True
                self.suporte_y = self.chao_y
                self.suporte_plataforma = None
                pousou = True

        if pousou:
            self.salto_ativo = False
            self.definir_estado("aterrissando")
        elif not self.no_chao:
            # ``cair`` é reservado para uma queda não iniciada pelo botão de
            # pulo. Durante um salto intencional, a animação correta continua
            # sendo ``pular`` até tocar o chão.
            self.definir_estado("pular" if self.salto_ativo else "cair")
        elif self._animacao_temporaria_ativa():
            pass
        elif self.estado == "respawn" and not self._animacao_temporaria_concluida():
            # O respawn continua visível por tempo suficiente para o jogador
            # perceber o retorno e não pode ser trocado por ``parada`` no
            # mesmo frame em que a entrada estiver neutra.
            pass
        elif self.estado == "abaixar":
            pass
        elif abs(self.vx) < 1:
            self.definir_estado("parada")
        elif self.estado not in ("derrapando", "aterrissando"):
            self.definir_estado("correr" if self.correndo else "andar")

        self.tempo_estado += dt
        self.animacoes[self.estado].atualizar(dt)
        self._atualizar_rect()

    def _tem_suporte(self, solidos):
        for solido in solidos:
            if solido.top != round(self.suporte_y):
                continue
            if self._horizontalmente_sobre(solido):
                return True
        return False

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
        if self.morto or (self.estado == "respawn" and not self._animacao_temporaria_concluida()):
            return
        self.morto = True
        self.motivo_morte = motivo
        self.vx = 0.0
        self.vy = 0.0
        self.correndo = False
        if motivo == "buraco" and self.caindo_no_buraco:
            self.definir_estado("buraco")
        else:
            self.definir_estado("morrendo")

    def iniciar_queda_buraco(self, largura_buraco=None):
        if not self.morto:
            self.caindo_no_buraco = True
            self.no_chao = False
            self.salto_ativo = False
            self.suporte_plataforma = None
            self.vx = 0.0
            self.vy = max(160.0, self.vy)
            self._ajustar_animacao_buraco(largura_buraco)
            self.definir_estado("buraco")

    def _ajustar_animacao_buraco(self, largura_buraco):
        """Escala a sequência do bueiro sem aumentar a personagem junto do vao."""
        if not self._quadros_buraco_base or not largura_buraco:
            return
        largura_base = max(quadro.get_width() for quadro in self._quadros_buraco_base)
        largura_disponivel = max(1, int(largura_buraco) - FOLGA_BUEIRO_ANIMACAO)
        largura_alvo = max(
            LARGURA_BUEIRO_ANIMACAO_MIN,
            min(LARGURA_BUEIRO_ANIMACAO_MAX - FOLGA_BUEIRO_ANIMACAO, largura_disponivel),
        )
        fator = largura_alvo / max(1, largura_base)
        if abs(fator - 1.0) < 0.02:
            quadros = list(self._quadros_buraco_base)
        else:
            tamanhos = [
                (max(1, round(quadro.get_width() * fator)), max(1, round(quadro.get_height() * fator)))
                for quadro in self._quadros_buraco_base
            ]
            largura_canvas = max(largura for largura, _ in tamanhos)
            altura_canvas = max(altura for _, altura in tamanhos)
            quadros = []
            for quadro, tamanho in zip(self._quadros_buraco_base, tamanhos):
                redimensionado = pygame.transform.smoothscale(quadro, tamanho)
                canvas = pygame.Surface((largura_canvas, altura_canvas), pygame.SRCALPHA)
                canvas.blit(redimensionado, ((largura_canvas - tamanho[0]) // 2, altura_canvas - tamanho[1]))
                quadros.append(canvas)
        self.animacoes["buraco"] = Animacao(quadros, 8, False)

    def reiniciar(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.correndo = False
        self.no_chao = True
        self.salto_ativo = False
        self.suporte_y = float(y)
        self.suporte_plataforma = None
        self.caindo_no_buraco = False
        self.morto = False
        self.motivo_morte = ""
        if self._quadros_buraco_base:
            self.animacoes["buraco"] = Animacao(self._quadros_buraco_base, 8, False)
        self.definir_estado("parada")
        self._atualizar_rect()

    def morreu_no_buraco(self, hitboxes):
        if self.caindo_no_buraco:
            return True
        if not self.no_chao:
            return False
        centro = self.rect.centerx
        return any(hitbox.left < centro < hitbox.right for hitbox in hitboxes)

    def queda_buraco_concluida(self):
        return self.caindo_no_buraco and self.animacoes["buraco"].concluida()

    def getRect(self):
        return self.rect.copy()

    def desenhar(self, tela, camera_x=0, alpha=255):
        imagem = self.animacoes[self.estado].imagem()
        if alpha != 255:
            imagem = imagem.copy()
            imagem.set_alpha(alpha)
        destino = imagem.get_rect(midbottom=(round(self.x - camera_x), round(self.y)))
        if self.estado == "buraco":
            # Os quadros de ``buraco`` têm alguns pixels transparentes abaixo
            # da calçada desenhada no próprio asset. Alinhamos o conteúdo
            # visível, e não a borda vazia do canvas, ao piso do jogo.
            limites = imagem.get_bounding_rect()
            destino.bottom += imagem.get_height() - limites.bottom
        tela.blit(imagem, destino)
