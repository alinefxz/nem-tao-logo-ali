import math

import pygame

from scripts.assets import carregar_animacao, carregar_imagem
from scripts.config import CHAO_Y


def _imagem_unica(pasta, nome, altura):
    return carregar_animacao(pasta, nome, altura)[0]


class Obstaculo:
    def __init__(self):
        self.hitbox = pygame.Rect(0, 0, 1, 1)
        self.danoso = True
        self.visivel = True
        self.tipo = "obstaculo"

    def atualizar(self, dt, mundo):
        pass

    def redefinir(self):
        pass

    def desenhar(self, tela, camera_x):
        pass


class Buraco(Obstaculo):
    def __init__(self, x, largura=110):
        super().__init__()
        self.x = x
        # A abertura precisa ser claramente maior que o pé da personagem e
        # ocupar a mesma faixa da calçada onde ela caminha.
        self.hitbox = pygame.Rect(x - largura / 2, CHAO_Y - 8, largura, 30)
        self.tipo = "buraco"
        self.largura = largura
        self.cor = (25, 25, 32)

    def desenhar(self, tela, camera_x):
        r = self.hitbox.move(-camera_x, 0)
        pygame.draw.ellipse(tela, (15, 15, 20), r.inflate(0, 12))
        pygame.draw.ellipse(tela, (10, 10, 12), r.inflate(-24, 4))
        pygame.draw.arc(tela, (60, 60, 70), r.inflate(-16, 6), 0, math.pi, 2)


class BuracoMovel(Obstaculo):
    def __init__(self, x_a, x_b, largura=110, banda=150):
        super().__init__()
        self.pos_a = x_a
        self.pos_b = x_b
        self.atual = 0
        self.largura = largura
        self.banda = banda
        self.cooldown = 0.0
        self.gatilho_usado = False
        self.tipo = "buraco_movel"
        self.buraco_visual = Buraco(0, largura)
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        x = self.pos_a if self.atual == 0 else self.pos_b
        self.buraco_visual.x = x
        self.buraco_visual.hitbox = pygame.Rect(
            x - self.largura / 2, CHAO_Y - 8, self.largura, 30
        )
        self.hitbox = self.buraco_visual.hitbox

    def atualizar(self, dt, mundo):
        self.cooldown = max(0.0, self.cooldown - dt)
        jogador = mundo.jogador
        if jogador.morto:
            return
        if jogador.no_chao:
            self.gatilho_usado = False
        if self.cooldown > 0:
            return
        dentro_banda = (
            self.pos_a - self.banda
            <= jogador.rect.centerx
            <= self.pos_a + self.banda
        )
        if dentro_banda and not self.gatilho_usado and not jogador.no_chao and jogador.vy < 0:
            self.atual = (self.atual + 1) % 2
            self._atualizar_hitbox()
            self.cooldown = 0.35
            self.gatilho_usado = True

    def redefinir(self):
        self.atual = 0
        self.cooldown = 0.0
        self.gatilho_usado = False
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        self.buraco_visual.desenhar(tela, camera_x)


class PlacaQueCai(Obstaculo):
    def __init__(self, x, altura=110, distancia_gatilho=360):
        super().__init__()
        self.x = x
        self.altura = altura
        self.imagem = _imagem_unica("cenario", "placa", altura)
        self.largura = self.imagem.get_width()
        self.y = -300.0
        self.estado = "suspensa"
        self.distancia_gatilho = distancia_gatilho
        self.inicial_y = -300.0
        self.tipo = "placa"

    def redefinir(self):
        self.estado = "suspensa"
        self.y = self.inicial_y
        self.visivel = True
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        if self.estado == "suspensa":
            self.hitbox = pygame.Rect(0, 0, 1, 1)
        else:
            self.hitbox = pygame.Rect(
                self.x - self.largura / 2, self.y, self.largura, self.altura
            )

    def atualizar(self, dt, mundo):
        jogador = mundo.jogador
        if self.estado == "suspensa":
            # O gatilho é horizontal e independe da altura da personagem:
            # pular perto da placa não é uma condição especial para derrubá-la.
            chegando = abs(jogador.rect.centerx - self.x) <= self.distancia_gatilho
            if not jogador.morto and chegando:
                self.estado = "caindo"
        elif self.estado == "caindo":
            self.y += 1500.0 * dt
            if self.y >= CHAO_Y - self.altura:
                self.y = CHAO_Y - self.altura
                self.estado = "caida"
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        pos = (round(self.x - camera_x - self.largura / 2), round(self.y))
        tela.blit(self.imagem, pos)


class ConeRolante(Obstaculo):
    def __init__(self, x_inicial, velocidade=200, altura=72, limites=None):
        super().__init__()
        self.quadros = carregar_animacao("cenario", "cone", altura)
        self.largura = self.quadros[0].get_width()
        self.altura = altura
        self.x = x_inicial
        self.velocidade = -velocidade
        self.limites = limites
        self.tempo_anim = 0.0
        self.tipo = "cone_rolante"
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        self.hitbox = pygame.Rect(
            self.x - self.largura / 2 + 6, CHAO_Y - self.altura + 4, self.largura - 12, self.altura - 4
        )

    def atualizar(self, dt, mundo):
        self.x += self.velocidade * dt
        self.tempo_anim += dt
        if self.limites is not None:
            if self.x <= self.limites[0]:
                self.x = self.limites[0]
                self.velocidade = abs(self.velocidade)
            elif self.x >= self.limites[1]:
                self.x = self.limites[1]
                self.velocidade = -abs(self.velocidade)
        elif self.x < mundo.limite_obstaculos[0] - 200:
            self.x = mundo.limite_obstaculos[1] + 40
        self._atualizar_hitbox()

    def redefinir(self):
        self.tempo_anim = 0.0

    def desenhar(self, tela, camera_x):
        indice = int(self.tempo_anim * 18) % len(self.quadros)
        imagem = self.quadros[indice]
        pos = (round(self.x - camera_x - self.largura / 2), round(CHAO_Y - self.altura))
        tela.blit(imagem, pos)


class ConesDeslizam(Obstaculo):
    def __init__(self, x_a, x_b, altura=72, velocidade=120, id_inicial=0):
        super().__init__()
        self.altura = altura
        self.quadros = carregar_animacao("cenario", "cone", altura)
        self.largura = self.quadros[0].get_width()
        self.x_a = x_a
        self.x_b = x_b
        self.x = x_a if id_inicial == 0 else x_b
        self.velocidade = velocidade if id_inicial == 0 else -velocidade
        self.tempo_anim = 0.0
        self.tipo = "cone_deslizante"
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        self.hitbox = pygame.Rect(
            self.x - self.largura / 2 + 6, CHAO_Y - self.altura + 4, self.largura - 12, self.altura - 4
        )

    def atualizar(self, dt, mundo):
        self.x += self.velocidade * dt
        self.tempo_anim += dt
        if self.x >= self.x_b and self.velocidade > 0:
            self.velocidade = -self.velocidade
        elif self.x <= self.x_a and self.velocidade < 0:
            self.velocidade = -self.velocidade
        self._atualizar_hitbox()

    def redefinir(self):
        self.tempo_anim = 0.0

    def desenhar(self, tela, camera_x):
        indice = int(self.tempo_anim * 12) % len(self.quadros)
        imagem = self.quadros[indice]
        pos = (round(self.x - camera_x - self.largura / 2), round(CHAO_Y - self.altura))
        tela.blit(imagem, pos)


class CalcadaFalsa(Obstaculo):
    def __init__(self, x, largura=150):
        super().__init__()
        self.danoso = False
        self.x = x
        self.altura = 46
        self.largura = largura
        self.imagem = _imagem_unica("cenario", "calcadafalsa", self.altura)
        self.imagem = pygame.transform.scale(self.imagem, (largura, self.altura))
        self.y = CHAO_Y - self.altura
        self.estado = "ativa"
        self.tempo = 0.0
        self.com_jogador = False
        self.tipo = "calcada_falsa"
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        self.rect = pygame.Rect(self.x, self.y, self.largura, self.altura)
        self.hitbox = pygame.Rect(self.x, self.y - 60, self.largura, 60 + self.altura)

    def atualizar(self, dt, mundo):
        if self.estado == "ativa":
            if self.com_jogador:
                self.estado = "tremendo"
                self.tempo = 0.0
        elif self.estado == "tremendo":
            self.tempo += dt
            if self.tempo >= 0.4:
                self.estado = "caindo"
                self.tempo = 0.0
        elif self.estado == "caindo":
            self.tempo += dt
            self.y += 400.0 * dt
            if self.tempo >= 1.4:
                self.estado = "oculta"
                self.y = CHAO_Y + 80
        self._atualizar_hitbox()

    def eh_solido(self):
        return self.estado in ("ativa", "tremendo")

    def redefinir(self):
        self.estado = "ativa"
        self.y = CHAO_Y - self.altura
        self.tempo = 0.0
        self.com_jogador = False
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        if self.estado == "oculta":
            return
        deslocamento = 0
        if self.estado == "tremendo" and int(self.tempo * 40) % 2 == 0:
            deslocamento = 3
        pos = (round(self.x - camera_x + deslocamento), round(self.y))
        tela.blit(self.imagem, pos)


class BarreiraTemporizada(Obstaculo):
    def __init__(self, x, periodo_baixo=1.6, periodo_alto=1.3):
        super().__init__()
        self.x = x
        self.altura_total = 120
        self.largura = 90
        self.imagem = _imagem_unica("cenario", "barreira", 120)
        self.periodo_baixo = periodo_baixo
        self.periodo_alto = periodo_alto
        self.fase = 0.0
        self.em_alto = False
        self.tipo = "barreira"
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        if self.em_alto:
            self.hitbox = pygame.Rect(0, 0, 1, 1)
            self.rect = pygame.Rect(self.x, -200, self.largura, 200)
        else:
            self.hitbox = pygame.Rect(self.x - self.largura / 2, CHAO_Y - self.altura_total, self.largura, self.altura_total)
            self.rect = self.hitbox.copy()

    def atualizar(self, dt, mundo):
        limite = self.periodo_alto if self.em_alto else self.periodo_baixo
        self.fase += dt
        if self.fase >= limite:
            self.fase = 0.0
            self.em_alto = not self.em_alto
            self._atualizar_hitbox()

    def redefinir(self):
        self.fase = 0.0
        self.em_alto = False
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        if self.em_alto:
            return
        pos = (round(self.x - camera_x - self.largura / 2), round(CHAO_Y - self.altura_total))
        tela.blit(self.imagem, pos)


class Carro(Obstaculo):
    def __init__(self, x, velocidade=260, sentido=-1, largura=220, altura=110, sprite="carro", acelerado=False):
        super().__init__()
        self.largura = largura
        self.altura = altura
        self.imagem = _imagem_unica("cenario", sprite, altura)
        self.imagem = pygame.transform.scale(self.imagem, (largura, altura))
        self.x = x
        self.base = velocidade
        self.dir = sentido
        self.acelerado = acelerado
        self.fator = 1.0
        self.travado = False
        self.velocidade = velocidade
        self.tipo = "carro"
        self._atualizar_hitbox()
        if sentido > 0:
            self.imagem = pygame.transform.flip(self.imagem, True, False)

    def _atualizar_hitbox(self):
        self.hitbox = pygame.Rect(
            self.x - self.largura / 2, CHAO_Y - self.altura + 14, self.largura, self.altura - 14
        )

    def atualizar(self, dt, mundo):
        jogador = mundo.jogador
        andamento = 0.0 if (self.travado and not self.acelerado) else 1.0
        if self.acelerado and not jogador.morto:
            if jogador.rect.centerx > self.x - 1500:
                self.fator = min(self.fator + 3.2 * dt, 3.2)
        self.x += self.base * self.fator * dt * self.dir * andamento
        limite_e, limite_d = mundo.limite_obstaculos
        if self.x < limite_e - 500:
            self.x = limite_d + 300
            self.fator = 1.0
        elif self.x > limite_d + 500:
            self.x = limite_e - 300
            self.fator = 1.0
        self._atualizar_hitbox()

    def redefinir(self):
        self.fator = 1.0

    def desenhar(self, tela, camera_x):
        pos = (round(self.x - camera_x - self.largura / 2), round(CHAO_Y - self.altura + 14))
        tela.blit(self.imagem, pos)


class Semaforo(Obstaculo):
    def __init__(self, x, periodo_verde=2.4, periodo_vermelho=1.8):
        super().__init__()
        self.x = x
        self.danoso = False
        self.imagem = _imagem_unica("cenario", "semaforo", 130)
        self.periodo_verde = periodo_verde
        self.periodo_vermelho = periodo_vermelho
        self.fase = 0.0
        self.verde = False
        self.tipo = "semaforo"
        self.poleiro = 320

    def permanente_verde(self, valor=True):
        self.verde = valor
        self.fase = 0.0

    def atualizar(self, dt, mundo):
        limite = self.periodo_verde if self.verde else self.periodo_vermelho
        self.fase += dt
        if self.fase >= limite:
            self.fase = 0.0
            self.verde = not self.verde

    def redefinir(self):
        self.verde = False
        self.fase = 0.0

    def desenhar(self, tela, camera_x):
        base_x = round(self.x - camera_x - self.imagem.get_width() / 2)
        base_y = CHAO_Y - self.poleiro
        tela.blit(self.imagem, (base_x, base_y))
        luz_x = base_x + self.imagem.get_width() // 2 - 4
        if self.verde:
            pygame.draw.circle(tela, (60, 220, 80), (luz_x, base_y + 20), 5)
        else:
            pygame.draw.circle(tela, (235, 60, 50), (luz_x, base_y + 20), 5)


class PocaEscorregadia(Obstaculo):
    def __init__(self, x, largura=180):
        super().__init__()
        self.danoso = False
        self.largura = largura
        self.hitbox = pygame.Rect(x - largura / 2, CHAO_Y - 26, largura, 26)
        self.tipo = "poca"
        self.aplicada = False
        self.max_x = x + largura / 2

    def atualizar(self, dt, mundo):
        jogador = mundo.jogador
        if jogador.morto:
            self.aplicada = False
            return
        if self.hitbox.colliderect(jogador.rect) and jogador.no_chao and not self.aplicada:
            self.aplicada = True
            jogador.derrapar()
        if jogador.rect.centerx > self.max_x:
            self.aplicada = False

    def redefinir(self):
        self.aplicada = False

    def desenhar(self, tela, camera_x):
        r = self.hitbox.move(-camera_x, 8)
        pygame.draw.ellipse(tela, (90, 130, 150), r.inflate(-20, -10))
        pygame.draw.ellipse(tela, (120, 160, 180), r.inflate(-60, -18))


class PlacaGiratoria(Obstaculo):
    def __init__(self, x, altura=110, periodo=2.2):
        super().__init__()
        self.x = x
        self.altura = altura
        self.imagem = _imagem_unica("cenario", "placa", altura)
        self.largura = self.imagem.get_width()
        self.pivo = (x, CHAO_Y)
        self.fase = 0.0
        self.periodo = periodo
        self.angulo = 0.0
        self.tipo = "placa_giratoria"
        self._atualizar_hitbox()

    def atualizar(self, dt, mundo):
        self.fase += dt
        ciclo = (self.fase % self.periodo) / self.periodo
        alvo = 0.0 if ciclo < 0.5 else 1.25
        passo = dt * 3.5
        diferenca = alvo - self.angulo
        self.angulo += max(-passo, min(passo, diferenca))
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        rot = renderizar_rotacionada(self.imagem, self.angulo)
        rect = rot.get_rect(midbottom=self.pivo)
        self.hitbox = rect.move(0, 0)

    def redefinir(self):
        self.fase = 0.0
        self.angulo = 0.0
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        rot = renderizar_rotacionada(self.imagem, self.angulo)
        rect = rot.get_rect(midbottom=(self.pivo[0] - camera_x, self.pivo[1]))
        tela.blit(rot, rect)


def renderizar_rotacionada(imagem, angulo_rad):
    return pygame.transform.rotate(imagem, math.degrees(angulo_rad))


class GalhoCaindo(Obstaculo):
    def __init__(self, x, intervalo=2.4, altura=92):
        super().__init__()
        self.x = x
        self.intervalo = intervalo
        self.imagem = _imagem_unica("cenario", "galho", altura)
        self.altura = altura
        self.largura = self.imagem.get_width()
        self.momento = 0.0
        self.estado = "espera"
        self.y = -120.0
        self.tempo_vida = 0.0
        self.tipo = "galho"
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        if self.estado == "espera":
            self.hitbox = pygame.Rect(0, 0, 1, 1)
        else:
            self.hitbox = pygame.Rect(self.x - self.largura / 2 + 14, self.y + 8, self.largura - 28, self.altura - 12)

    def atualizar(self, dt, mundo):
        self.momento += dt
        if self.estado == "espera" and self.momento >= self.intervalo:
            self.estado = "caindo"
            self.momento = 0.0
        elif self.estado == "caindo":
            self.y += 1400.0 * dt
            if self.y >= CHAO_Y - self.altura:
                self.y = CHAO_Y - self.altura
                self.estado = "chao"
        elif self.estado == "chao":
            self.tempo_vida += dt
            if self.tempo_vida >= 1.3:
                self.estado = "espera"
                self.y = -120.0
                self.tempo_vida = 0.0
        self._atualizar_hitbox()

    def redefinir(self):
        self.estado = "espera"
        self.y = -120.0
        self.momento = 0.0
        self.tempo_vida = 0.0
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        if self.estado == "espera":
            return
        pos = (round(self.x - camera_x - self.largura / 2), round(self.y))
        tela.blit(self.imagem, pos)


class Pendulo(Obstaculo):
    def __init__(self, x, comprimento=170, amplitude=0.9, periodo=2.3):
        super().__init__()
        self.x = x
        self.comprimento = comprimento
        self.amplitude = amplitude
        self.periodo = periodo
        self.fase = 0.0
        self.carga = _imagem_unica("cenario", "pendulo", 92)
        self.tipo = "pendulo"
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        ang = self.angulo_atual()
        px = self.x + math.sin(ang) * self.comprimento
        py = CHAO_Y - 330 + (1 - math.cos(ang)) * self.comprimento
        w, h = self.carga.get_size()
        self.peso_centro = (px, py)
        self.hitbox = pygame.Rect(px - w / 2 + 10, py - h / 2 + 8, w - 20, h - 16)

    def angulo_atual(self):
        return self.amplitude * math.sin((self.fase / self.periodo) * 2 * math.pi)

    def atualizar(self, dt, mundo):
        self.fase += dt
        self._atualizar_hitbox()

    def redefinir(self):
        self.fase = 0.0
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        ang = self.angulo_atual()
        px = self.x + math.sin(ang) * self.comprimento
        py = CHAO_Y - 330 + (1 - math.cos(ang)) * self.comprimento
        topo = (self.x - camera_x, CHAO_Y - 330)
        peso = (px - camera_x, py)
        pygame.draw.line(tela, (70, 70, 80), topo, peso, 3)
        tela.blit(self.carga, (peso[0] - self.carga.get_width() / 2, peso[1] - self.carga.get_height() / 2))


class PlataformaAfastada(Obstaculo):
    def __init__(self, x, largura=220, distancia=320, gatilho_dist=330):
        super().__init__()
        self.largura = largura
        self.altura = 46
        self.x_inicial = x
        self.x = x
        self.offset = 0.0
        self.gatilho_dist = gatilho_dist
        self.distancia = distancia
        self.imagem = _imagem_unica("cenario", "calcadafalsa", self.altura)
        self.imagem = pygame.transform.scale(self.imagem, (largura, self.altura))
        self.y = CHAO_Y - self.altura
        self.ativo = False
        self.danoso = False
        self.xs_offset = 0.0
        self.tipo = "plataforma_afastada"
        self._atualizar_hitbox()

    def _atualizar_hitbox(self):
        self.rect = pygame.Rect(self.x + self.xs_offset, self.y, self.largura, self.altura)
        self.hitbox = self.rect.copy()

    def atualizar(self, dt, mundo):
        jogador = mundo.jogador
        if jogador.morto:
            return
        if not self.ativo and not jogador.morto:
            distancia = abs(jogador.rect.centerx - (self.x + self.offset + self.largura / 2))
            if distancia < self.gatilho_dist:
                self.ativo = True
        if self.ativo:
            self.xs_offset = min(self.xs_offset + 420.0 * dt, self.distancia)
        self._atualizar_hitbox()

    def eh_solido(self):
        return True

    def redefinir(self):
        self.ativo = False
        self.xs_offset = 0.0
        self._atualizar_hitbox()

    def desenhar(self, tela, camera_x):
        if not self.eh_solido():
            return
        pos = (round(self.x + self.xs_offset - camera_x), round(self.y))
        tela.blit(self.imagem, pos)


class TrianguloFixo(Obstaculo):
    def __init__(self, x, altura=95):
        super().__init__()
        self.altura = altura
        self.imagem = _imagem_unica("cenario", "triangulo", altura)
        self.largura = self.imagem.get_width()
        self.x = x
        self.tipo = "triangulo"
        # O desenho tem uma haste alta, mas ela é decoração. O perigo é a
        # base do sinal; usando uma hitbox baixa o jogador consegue saltar
        # por cima sem ser atingido no meio do ar.
        base_largura = max(18, int(self.largura * 0.42))
        self.hitbox = pygame.Rect(
            round(x - base_largura / 2),
            CHAO_Y - 24,
            base_largura,
            24,
        )

    def desenhar(self, tela, camera_x):
        pos = (round(self.x - camera_x - self.largura / 2), round(CHAO_Y - self.altura))
        tela.blit(self.imagem, pos)


class Porta(Obstaculo):
    def __init__(self, x, altura=150):
        super().__init__()
        self.x = x
        self.danoso = False
        self.altura = altura
        self.quadros = carregar_animacao("personagem", "porta", altura)
        self.imagem = self.quadros[0]
        self.largura = self.quadros[0].get_width()
        self.hitbox = pygame.Rect(x - self.largura / 2, CHAO_Y - self.altura, self.largura, self.altura)
        self.tipo = "porta"
        self.alcançada = False
        self.tempo_anim = 0.0

    def atualizar(self, dt, mundo):
        self.tempo_anim += max(0.0, dt)
        if not self.alcançada and not mundo.jogador.morto and self.hitbox.colliderect(mundo.jogador.rect):
            self.alcançada = True
            mundo.concluir_fase()

    def redefinir(self):
        self.alcançada = False
        self.tempo_anim = 0.0

    def desenhar(self, tela, camera_x):
        indice = min(len(self.quadros) - 1, int(self.tempo_anim * 10))
        imagem = self.quadros[indice]
        pos = (round(self.x - camera_x - self.largura / 2), round(CHAO_Y - self.altura))
        tela.blit(imagem, pos)


class CheckpointObjeto(Obstaculo):
    def __init__(self, x):
        super().__init__()
        self.x = x
        self.danoso = False
        self.altura = 150
        self.hitbox = pygame.Rect(x - 30, CHAO_Y - self.altura - 40, 60, self.altura + 60)
        self.ativo = False
        self.tipo = "checkpoint"

    def atualizar(self, dt, mundo):
        if not self.ativo and not mundo.jogador.morto and self.hitbox.colliderect(mundo.jogador.rect):
            self.ativo = True
            mundo.ativar_checkpoint(self.x, self)

    def redefinir(self):
        pass

    def desenhar(self, tela, camera_x):
        base = (round(self.x - camera_x), CHAO_Y)
        topo_y = CHAO_Y - self.altura
        pygame.draw.line(tela, (220, 220, 230), base, (base[0], topo_y), 4)
        if self.ativo:
            cor = (60, 220, 120)
        else:
            cor = (220, 220, 230)
        pontos = [
            (base[0], topo_y),
            (base[0] + 34, topo_y + 18),
            (base[0], topo_y + 36),
        ]
        pygame.draw.polygon(tela, cor, pontos)
        pygame.draw.rect(tela, (200, 120, 40), (base[0] - 5, CHAO_Y - 8, 10, 8))
