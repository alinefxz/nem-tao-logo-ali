import pygame

from scripts.assets import carregar_calcada
from scripts.config import (
    ALTURA,
    ALTURA_RUA,
    CHAO_Y,
    COR_ARVORE,
    COR_CEU_1,
    COR_CEU_2,
    COR_ASFALTO,
    COR_TERRA,
    LARGURA,
    NOMES_FASES,
)
from scripts.fases_planos import adicionar_marcadores, contruir_plano
from scripts.jogador import Jogador
from scripts.obstaculos import (
    Buraco,
    BuracoMovel,
    CalcadaFalsa,
    Carro,
    PlataformaAfastada,
    Porta,
    Semaforo,
)
from scripts.pontuacao import GerenciadorPontuacao
from scripts.tempo import GerenciadorTempo


class Fase:
    def __init__(self, indice, pontuacao=None, tempo=None):
        self.indice = indice
        self.plano = contruir_plano(indice)
        self.largura_mundo = self.plano["largura"]
        self.pontuacao = pontuacao or GerenciadorPontuacao()
        self.tempo = tempo or GerenciadorTempo()
        self.pontuacao.nova_fase()
        self.tempo.iniciar_fase(indice)

        self.buracos = []
        for x, w in self.plano["buracos"]:
            self.buracos.append(Buraco(x, w))
        for x_a, x_b, w, banda in self.plano["buraco_moveis"]:
            self.buracos.append(BuracoMovel(x_a, x_b, w, banda))

        self.obstaculos = list(self.plano["obstaculos"])
        adicionar_marcadores(self.plano, self)
        self.porta = next(o for o in self.obstaculos if isinstance(o, Porta))
        self.checkpoints = [o for o in self.obstaculos if o.tipo == "checkpoint"]
        self.checkpoints_marcados = set()

        self.spawn_x = self.plano["spawn"]
        self.respawn_x = self.spawn_x
        self.jogador = Jogador(self.spawn_x, CHAO_Y)

        self.camera_x = 0.0
        self.limite_obstaculos = (-200, self.largura_mundo + 200)
        self.tempo_morte = 0.0
        self.concluida = False
        self.concluida_tempo = 0.0
        self.resultado = None
        self.calcada_tile = None
        self._preparar_calcada()

    def _preparar_calcada(self):
        imagem = carregar_calcada()
        if imagem is not None:
            # O PNG possui transparência nas bordas para permitir uso como
            # sprite isolado. Para uma calçada repetida, recortamos somente a
            # área desenhada e colocamos uma faixa contínua atrás da textura.
            limites = imagem.get_bounding_rect(min_alpha=1)
            if limites.width == 0 or limites.height == 0:
                return
            imagem = imagem.subsurface(limites).copy()
            altura_tile = min(58, ALTURA - CHAO_Y)
            escala = altura_tile / imagem.get_height()
            largura_tile = max(260, int(imagem.get_width() * escala))
            self.calcada_tile = (pygame.transform.smoothscale(imagem, (largura_tile, altura_tile)), largura_tile)

    def redefinir_obstaculos(self):
        for o in self.buracos + self.obstaculos:
            o.redefinir()

    def ativar_checkpoint(self, x, objeto):
        if objeto not in self.checkpoints_marcados:
            self.checkpoints_marcados.add(objeto)
            self.pontuacao.checkpoint(False)
        self.respawn_x = x

    def atacar_jogador(self):
        # Durante o retorno, a personagem fica protegida. Caso contrário um
        # obstáculo no próprio ponto de checkpoint poderia matar o jogador
        # antes de a animação de respawn terminar.
        if self.jogador.estado == "respawn":
            return False
        for o in self.buracos + self.obstaculos:
            if isinstance(o, (Buraco, BuracoMovel)):
                continue
            if o.danoso and o.visivel and o.hitbox.colliderect(self.jogador.rect):
                return True
        return False

    def _iniciar_queda_no_buraco(self):
        jogador = self.jogador
        if jogador.morto or not jogador.no_chao:
            return
        centro = jogador.rect.centerx
        for buraco in self.buracos:
            # Encostar com a lateral ainda é seguro; a queda começa quando
            # os pés passam para dentro do vão.
            margem = min(8, max(1, buraco.hitbox.width // 5))
            if buraco.hitbox.left + margem < centro < buraco.hitbox.right - margem:
                jogador.iniciar_queda_buraco(buraco.largura)
                return

    def atualizar(self, dt, teclas, pulou):
        if self.concluida:
            self.concluida_tempo += dt
            return
        jogador = self.jogador

        esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        correndo = teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
        abaixou = teclas[pygame.K_s] or teclas[pygame.K_DOWN]
        if abaixou and not esquerda and not direita:
            jogador.abaixar()
        elif esquerda and not direita:
            jogador.mover(-1, correndo)
        elif direita and not esquerda:
            jogador.mover(1, correndo)
        else:
            jogador.mover(0, correndo)
        if pulou:
            jogador.pular()

        self.tempo.acumular(dt)

        plataformas = [
            o.rect
            for o in self.obstaculos
            if isinstance(o, (CalcadaFalsa, PlataformaAfastada))
            and o.eh_solido()
        ]
        solidos = []
        for o in self.obstaculos:
            if isinstance(o, Buraco) or isinstance(o, BuracoMovel):
                continue
            if hasattr(o, "rect") and o.danoso and o.tipo == "barreira":
                solidos.append(o.rect)

        jogador.atualizar(dt, solidos, plataformas)
        jogador.x = max(20.0, min(self.largura_mundo - 20.0, jogador.x))

        for o in self.buracos + self.obstaculos:
            o.atualizar(dt, self)

        self._atualizar_carros_gate()
        self._atualizar_plataformas_contato()
        self._iniciar_queda_no_buraco()

        if jogador.morreu_no_buraco([b.hitbox for b in self.buracos]):
            # A entrada no vão inicia a sequência visual; a morte só é
            # registrada quando a animação de sete quadros termina.
            if jogador.queda_buraco_concluida():
                self._registrar_morte("buraco")
        elif self.atacar_jogador():
            self._registrar_morte("morte")
        elif jogador.y > ALTURA + 250:
            self._registrar_morte("buraco" if jogador.caindo_no_buraco else "morte")

        if jogador.morto:
            self.tempo_morte += dt
            duracao = 1.0 if jogador.motivo_morte == "buraco" else 0.9
            if self.tempo_morte >= duracao:
                self._reexibir_jogador()
        else:
            self.tempo_morte = 0.0

        self.camera_x = max(
            0.0,
            min(
                jogador.x - LARGURA * 0.28,
                self.largura_mundo - LARGURA,
            ),
        )

    def _registrar_morte(self, motivo):
        jogador = self.jogador
        if jogador.morto:
            return
        self.pontuacao.registrar_morte()
        jogador.morrer(motivo)

    def _reexibir_jogador(self):
        self.jogador.reiniciar(self.respawn_x, CHAO_Y)
        self.jogador.definir_estado("respawn")
        self.redefinir_obstaculos()

    def _atualizar_carros_gate(self):
        semaforos = [o for o in self.obstaculos if isinstance(o, Semaforo)]
        carros = [o for o in self.obstaculos if isinstance(o, Carro)]
        if not semaforos:
            return
        semaforo = semaforos[0]
        for carro in carros:
            pertence = (semaforo.x - 800) <= carro.x <= (semaforo.x + 600)
            carro.travado = pertence and not semaforo.verde

    def _atualizar_plataformas_contato(self):
        for o in self.obstaculos:
            if isinstance(o, CalcadaFalsa) and o.eh_solido():
                if (
                    self.jogador.no_chao
                    and self.jogador.rect.bottom == o.rect.top
                    and self.jogador.rect.colliderect(o.rect)
                ):
                    o.com_jogador = True

    def concluir_fase(self):
        if self.concluida:
            return
        self.concluida = True
        self.tempo.concluir_fase()
        bonus = self.tempo.bonus_fase(self.indice)
        ganhos = self.pontuacao.concluir_fase(bonus)
        self.resultado = {
            "fase": self.indice,
            "ganhos": ganhos,
            "bonus_tempo": bonus,
            "sem_mortes": self.pontuacao.mortes_fase == 0,
            "tempo_fase": self.tempo.tempo_fase(),
        }

    def desenhar_fundo(self, tela):
        for y in range(0, CHAO_Y):
            t = y / CHAO_Y
            r = int(COR_CEU_1[0] + (COR_CEU_2[0] - COR_CEU_1[0]) * t)
            g = int(COR_CEU_1[1] + (COR_CEU_2[1] - COR_CEU_1[1]) * t)
            b = int(COR_CEU_1[2] + (COR_CEU_2[2] - COR_CEU_1[2]) * t)
            pygame.draw.line(tela, (r, g, b), (0, y), (LARGURA, y))
        if self.indice == 0:
            self._desenhar_rua(tela)
        elif self.indice == 1:
            self._desenhar_obras(tela)
        elif self.indice == 2:
            self._desenhar_avenida(tela)
        elif self.indice == 3:
            self._desenhar_parque(tela)
        else:
            self._desenhar_quarteirao(tela)

    def _fundo_parallax(self, tela, deslocamento, espessura, cor):
        passo = 380
        comeco = int((self.camera_x * deslocamento) // passo) * passo
        y = CHAO_Y - 190
        x = comeco
        while x < LARGURA + (self.camera_x * deslocamento) + passo:
            sx = round(x - self.camera_x * deslocamento)
            pygame.draw.rect(tela, cor, (sx, y - 110, 130, espessura))
            x += passo

    def _desenhar_prédios(self, tela, escala=1.0, topo_min=120, topo_max=300, cor=(90, 100, 120)):
        passo = 300
        start = int(self.camera_x * 0.5)
        comeco = (start // passo) * passo
        import random
        rng = random.Random(self.indice * 97)
        alturas = {i: rng.randint(topo_min, topo_max) for i in range(0, 6000, passo)}
        x = comeco
        while x - self.camera_x * 0.5 < LARGURA + passo:
            topo = alturas.get((x // passo) * passo, 200)
            sx = round(x - self.camera_x * 0.5)
            pygame.draw.rect(tela, cor, (sx - 40, CHAO_Y - topo - 10, 150, topo + 60))
            cor_esc = tuple(max(0, c - 25) for c in cor)
            pygame.draw.rect(tela, cor_esc, (sx - 20, CHAO_Y - topo + 30, 30, 40))
            x += passo

    def _desenhar_rua(self, tela):
        self._desenhar_prédios(tela, cor=(120, 130, 145))
        for i in range(3):
            y = 240 + i * 70
            pygame.draw.rect(tela, (200, 210, 90), (0, y, LARGURA, 3))

    def _desenhar_obras(self, tela):
        self._desenhar_prédios(tela, cor=(110, 125, 130))
        passo = 260
        start = int(self.camera_x * 0.5)
        x = (start // passo) * passo
        while x - self.camera_x * 0.5 < LARGURA + passo:
            sx = round(x - self.camera_x * 0.5)
            pygame.draw.line(tela, (40, 40, 45), (sx, CHAO_Y - 300), (sx, CHAO_Y - 60), 4)
            pygame.draw.polygon(tela, (60, 60, 60), [(sx, CHAO_Y - 300), (sx + 40, CHAO_Y - 330), (sx + 80, CHAO_Y - 300)])
            x += passo

    def _desenhar_avenida(self, tela):
        self._desenhar_prédios(tela, cor=(100, 105, 125))
        pygame.draw.rect(tela, COR_TERRA, (0, CHAO_Y - 42, LARGURA, 42))
        passo = 90
        start = int(self.camera_x)
        x = (start // passo) * passo
        while x - self.camera_x < LARGURA + passo:
            sx = round(x - self.camera_x)
            pygame.draw.rect(tela, (210, 210, 210), (sx + 12, CHAO_Y - 20, 45, 5))
            x += passo

    def _desenhar_parque(self, tela):
        passo = 300
        start = int(self.camera_x * 0.45)
        x = (start // passo) * passo
        rng = __import__("random").Random(self.indice * 53)
        alturas = {i: rng.randint(200, 330) for i in range(-600, 6000, passo)}
        while x - self.camera_x * 0.45 < LARGURA + passo:
            h = alturas.get((x // passo) * passo, 260)
            sx = round(x - self.camera_x * 0.45)
            pygame.draw.rect(tela, (90, 70, 55), (sx - 10, CHAO_Y - h + 60, 26, h - 60))
            pygame.draw.circle(tela, COR_ARVORE, (sx + 4, CHAO_Y - h), 95)
            pygame.draw.circle(tela, (70, 140, 85), (sx - 40, CHAO_Y - h + 30), 60)
            x += passo

    def _desenhar_quarteirao(self, tela):
        self._desenhar_prédios(tela, cor=(110, 95, 110))
        passo = 260
        start = int(self.camera_x * 0.5)
        x = (start // passo) * passo
        while x - self.camera_x * 0.5 < LARGURA + passo:
            sx = round(x - self.camera_x * 0.5)
            pygame.draw.polygon(tela, (40, 40, 45), [(sx, CHAO_Y), (sx + 70, CHAO_Y - 120), (sx + 140, CHAO_Y)])
            x += passo
        self._desenhar_casa(tela)

    def _desenhar_casa(self, tela):
        """Desenha a casa no lado final do mundo, alinhada à porta de chegada."""
        sx = round(self.porta.x - self.camera_x)
        largura = 360
        esquerda = sx - 90
        base = CHAO_Y
        pygame.draw.rect(tela, (191, 143, 104), (esquerda, base - 210, largura, 210))
        pygame.draw.polygon(
            tela,
            (105, 55, 68),
            [(esquerda - 28, base - 210), (esquerda + largura // 2, base - 350), (esquerda + largura + 28, base - 210)],
        )
        pygame.draw.rect(tela, (88, 57, 50), (sx - 42, base - 142, 84, 142))
        pygame.draw.circle(tela, (238, 194, 93), (sx + 25, base - 72), 6)
        for janela_x in (esquerda + 54, esquerda + largura - 112):
            pygame.draw.rect(tela, (119, 190, 211), (janela_x, base - 155, 58, 56))
            pygame.draw.line(tela, (245, 230, 196), (janela_x + 29, base - 155), (janela_x + 29, base - 99), 4)
            pygame.draw.line(tela, (245, 230, 196), (janela_x, base - 127), (janela_x + 58, base - 127), 4)
        pygame.draw.rect(tela, (82, 119, 71), (esquerda - 22, base - 32, largura + 44, 32))

    def desenhar_chao(self, tela):
        if self.calcada_tile is None:
            pygame.draw.rect(tela, COR_ASFALTO, (0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
            return
        tile, passo = self.calcada_tile
        topo_calcada = ALTURA - tile.get_height()
        # A faixa contínua elimina os vãos triangulares das extremidades
        # transparentes do sprite e mantém todo o piso no mesmo nível.
        topo_rua = max(0, CHAO_Y - ALTURA_RUA)
        pygame.draw.rect(tela, COR_ASFALTO, (0, topo_rua, LARGURA, CHAO_Y - topo_rua))
        pygame.draw.rect(tela, (91, 79, 70), (0, topo_calcada, LARGURA, ALTURA - topo_calcada))
        start = int(self.camera_x // passo) * passo
        x = start
        while x - self.camera_x < LARGURA:
            tela.blit(tile, (round(x - self.camera_x), topo_calcada))
            x += passo
        pygame.draw.line(tela, (38, 39, 43), (0, CHAO_Y), (LARGURA, CHAO_Y), 3)
        pygame.draw.line(tela, (62, 55, 51), (0, topo_calcada), (LARGURA, topo_calcada), 2)

    def desenhar_obstaculos(self, tela):
        jogador_no_buraco = self.jogador.caindo_no_buraco
        centro_jogador = self.jogador.rect.centerx
        for o in self.buracos + self.obstaculos:
            if (
                jogador_no_buraco
                and isinstance(o, (Buraco, BuracoMovel))
                and o.hitbox.left <= centro_jogador <= o.hitbox.right
            ):
                # A sequência ``buraco`` já traz a abertura e um pedaço da
                # calçada. Desenhar o ellipse procedural por baixo ao mesmo
                # tempo criava dois bueiros desalinhados.
                continue
            if o.tipo == "porta":
                continue
            o.desenhar(tela, self.camera_x)
        self.porta.desenhar(tela, self.camera_x)

    def desenhar_hud(self, tela):
        cx = COR_CEU_2
        painel = pygame.Surface((300, 92), pygame.SRCALPHA)
        painel.fill((20, 30, 50, 160))
        tela.blit(painel, (10, 10))
        import pygame as pg
        f1 = pg.font.SysFont("consolas", 22, bold=True)
        f2 = pg.font.SysFont("consolas", 18)
        nome = NOMES_FASES[self.indice]
        tela.blit(f1.render(f"Fase {self.indice + 1}/5 - {nome}", True, (255, 255, 255)), (20, 16))
        tela.blit(
            f2.render(
                f"Pontos: {self.pontuacao.pontos}   Mortes: {self.pontuacao.total_mortes}   Tempo: {int(self.tempo.tempo_fase()):02d}s",
                True,
                (230, 230, 235),
            ),
            (20, 52),
        )
        tela.blit(f2.render("A/D andar | Shift correr | Espaço pular | Esc pausa | R reiniciar", True, (200, 200, 210)), (20, 78))

    def desenhar(self, tela):
        self.desenhar_fundo(tela)
        self.desenhar_chao(tela)
        self.desenhar_obstaculos(tela)
        alpha = 255
        if self.jogador.estado == "respawn":
            alpha = 120
        self.jogador.desenhar(tela, self.camera_x, alpha=alpha)
        self.desenhar_hud(tela)
