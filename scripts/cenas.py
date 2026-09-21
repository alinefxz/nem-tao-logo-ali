"""Cenas e fluxo principal do jogo.

O módulo mantém a lógica de apresentação separada da simulação de ``Fase``.
Cada cena recebe o objeto ``Jogo`` e devolve o nome da próxima cena quando
precisa trocar de tela.
"""

import pygame

from scripts.config import (
    ALTURA,
    COR_CEU_1,
    COR_FUNDO,
    COR_TEXTO,
    LARGURA,
    NOMES_FASES,
)
from scripts.cliente_django import ClienteDjango
from scripts.fase import Fase
from scripts.interfaces import Botao
from scripts.pontuacao import GerenciadorPontuacao
from scripts.tempo import GerenciadorTempo


def _fonte(tamanho, negrito=False):
    pygame.font.init()
    return pygame.font.SysFont("segoeui", tamanho, bold=negrito)


def _texto(tela, texto, posicao, tamanho=28, cor=COR_TEXTO, centro=False, negrito=False):
    fonte = _fonte(tamanho, negrito)
    imagem = fonte.render(str(texto), True, cor)
    rect = imagem.get_rect()
    if centro:
        rect.center = posicao
    else:
        rect.topleft = posicao
    if tela is not None:
        tela.blit(imagem, rect)
    return rect


class Cena:
    def __init__(self, jogo):
        self.jogo = jogo
        self.tela = getattr(jogo, "tela", None)

    def entrar(self):
        pass

    def atualizar(self, dt, teclas, eventos):
        del dt, teclas, eventos
        return None

    def desenhar(self, tela=None):
        del tela

    def _tela(self, tela=None):
        return tela or self.tela


class MenuCena(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        self.botoes = []
        self.entrar()

    def entrar(self):
        tela = self._tela()
        self.botoes = [
            Botao(tela, "Jogar", 490, 280, 28, (53, 104, 165), COR_TEXTO, 300, 52),
            Botao(tela, "Instruções", 490, 346, 28, (53, 104, 165), COR_TEXTO, 300, 52),
            Botao(tela, "Ranking", 490, 412, 28, (53, 104, 165), COR_TEXTO, 300, 52),
            Botao(tela, "Sair", 490, 478, 28, (112, 70, 82), COR_TEXTO, 300, 52),
        ]

    def atualizar(self, dt, teclas, eventos):
        del dt, teclas
        if self.botoes[0].get_click(eventos):
            return "identificacao"
        if self.botoes[1].get_click(eventos):
            return "instrucoes"
        if self.botoes[2].get_click(eventos):
            return "ranking"
        if self.botoes[3].get_click(eventos):
            return "sair"
        return None

    def desenhar(self, tela=None):
        tela = self._tela(tela)
        if tela is None:
            return
        _fundo_menu(tela)
        _texto(tela, "NEM TÃO LOGO ALI", (640, 118), 54, (255, 246, 218), True, True)
        _texto(tela, "Uma caminhada curta. Um caminho que discorda.", (640, 172), 22, (215, 232, 244), True)
        for botao in self.botoes:
            botao.desenhar(tela)
        _texto(tela, "A/D ou setas para andar  •  Espaço para pular", (640, 665), 18, (200, 220, 235), True)


class InstrucoesCena(Cena):
    def entrar(self):
        self.voltar = Botao(self._tela(), "Voltar", 490, 590, 25, (53, 104, 165), COR_TEXTO, 300, 50)

    def atualizar(self, dt, teclas, eventos):
        del dt, teclas
        if self.voltar.get_click(eventos) or any(
            e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN) for e in eventos
        ):
            return "menu"
        return None

    def desenhar(self, tela=None):
        tela = self._tela(tela)
        if tela is None:
            return
        _fundo_menu(tela)
        _texto(tela, "COMO CHEGAR EM CASA", (640, 78), 42, (255, 246, 218), True, True)
        linhas = [
            ("A / D ou setas", "andar para a esquerda e para a direita"),
            ("Shift", "correr; sem Shift, a personagem caminha"),
            ("Espaço, W ou ↑", "pular obstáculos e atravessar buracos"),
            ("S ou ↓", "abaixar quando o cenário pedir"),
            ("Esc", "pausar a fase ou voltar ao menu"),
            ("R", "reiniciar rapidamente a fase atual"),
            ("Objetivo", "vencer cinco fases e alcançar a porta de casa"),
            ("Pontuação", "+300 por fase, bônus por tempo e poucas mortes"),
        ]
        y = 160
        for titulo, descricao in linhas:
            _texto(tela, titulo, (245, y), 24, (255, 214, 111), False, True)
            _texto(tela, descricao, (505, y + 2), 22, (235, 240, 245))
            y += 58
        self.voltar.desenhar(tela)


class IdentificacaoCena(Cena):
    def entrar(self):
        self.nome = ""
        self.mensagem = "Digite um apelido com até 20 caracteres."

    def processar_evento(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_BACKSPACE:
            self.nome = self.nome[:-1]
            return
        if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return
        caractere = getattr(evento, "unicode", "") or ""
        if not caractere.isprintable():
            return
        if not self.nome and caractere.isspace():
            return
        self.nome = (self.nome + caractere).strip()[:20]

    def _confirmar(self):
        nome = self.nome.strip()[:20]
        if not nome:
            self.mensagem = "O apelido não pode ficar vazio."
            return None
        self.nome = nome
        self.jogo.iniciar_partida(nome)
        return "jogo"

    def atualizar(self, dt, teclas, eventos):
        del dt, teclas
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return "menu"
            if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                destino = self._confirmar()
                if destino:
                    return destino
            else:
                self.processar_evento(evento)
        return None

    def desenhar(self, tela=None):
        tela = self._tela(tela)
        if tela is None:
            return
        _fundo_menu(tela)
        _texto(tela, "QUEM ESTÁ VOLTANDO?", (640, 160), 42, (255, 246, 218), True, True)
        caixa = pygame.Rect(360, 270, 560, 72)
        pygame.draw.rect(tela, (240, 245, 248), caixa, border_radius=8)
        pygame.draw.rect(tela, (255, 214, 111), caixa, 3, border_radius=8)
        _texto(tela, self.nome or "Digite seu apelido...", (390, 292), 30, (45, 55, 70) if self.nome else (130, 145, 160))
        _texto(tela, self.mensagem, (640, 390), 20, (220, 230, 240), True)
        _texto(tela, "Enter confirma  •  Esc volta", (640, 500), 20, (200, 220, 235), True)


class JogoCena(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        self.pontuacao = None
        self.tempo = None
        self.fase = None
        self.fase_atual = 0
        self.transicao = None
        self.pausado = False
        self.nome = ""
        self.botao_menu = None

    def entrar(self):
        if self.fase is None:
            self.iniciar(getattr(self.jogo, "nome_jogador", "Jogador"))

    def iniciar(self, nome):
        self.nome = str(nome).strip()[:20] or "Jogador"
        self.pontuacao = GerenciadorPontuacao()
        self.tempo = GerenciadorTempo()
        self.fase_atual = 0
        self.transicao = None
        self.pausado = False
        self.botao_menu = Botao(self._tela(), "Voltar ao menu", 490, 385, 22, (112, 70, 82), COR_TEXTO, 300, 48)
        self.fase = Fase(0, self.pontuacao, self.tempo)
        self.jogo.pontuacao = self.pontuacao
        self.jogo.tempo = self.tempo

    def _reiniciar_fase(self):
        # Reiniciar não apaga mortes nem bônus de checkpoint já recebidos.
        # Assim, a tentativa continua contando para o bônus de fase sem mortes.
        self.fase.redefinir_obstaculos()
        self.fase.jogador.reiniciar(self.fase.spawn_x, self.fase.jogador.chao_y)
        self.fase.respawn_x = self.fase.spawn_x
        self.fase.tempo_morte = 0.0
        self.fase.concluida = False
        self.fase.concluida_tempo = 0.0
        self.fase.resultado = None
        self.tempo.iniciar_fase(self.fase_atual)
        self.pausado = False
        self.transicao = None

    def _processar_eventos(self, eventos):
        pulou = False
        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue
            if evento.key == pygame.K_ESCAPE:
                self.pausado = not self.pausado
            elif evento.key == pygame.K_r and self.fase is not None:
                self._reiniciar_fase()
            elif evento.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                pulou = True
        return pulou

    def atualizar(self, dt, teclas, eventos):
        if self.pausado and self.botao_menu and self.botao_menu.get_click(eventos):
            return "menu"
        pulou = self._processar_eventos(eventos)
        if self.fase is None:
            return "menu"
        if self.pausado:
            return None
        self.fase.atualizar(dt, teclas, pulou)
        if not self.fase.concluida:
            return None
        if self.fase_atual < len(NOMES_FASES) - 1:
            self.fase_atual += 1
            self.transicao = f"Fase {self.fase_atual + 1}: {NOMES_FASES[self.fase_atual]}"
            self.fase = Fase(self.fase_atual, self.pontuacao, self.tempo)
            return None
        self.jogo.finalizar_partida(self.pontuacao, self.tempo)
        return "resultado"

    def desenhar(self, tela=None):
        tela = self._tela(tela)
        if tela is None or self.fase is None:
            return
        self.fase.desenhar(tela)
        if self.pausado:
            camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            camada.fill((8, 14, 28, 180))
            tela.blit(camada, (0, 0))
            _texto(tela, "PAUSADO", (640, 230), 54, (255, 246, 218), True, True)
            _texto(tela, "Esc continua  •  R reinicia a fase", (640, 310), 22, COR_TEXTO, True)
            if self.botao_menu:
                self.botao_menu.desenhar(tela)
        elif self.transicao:
            _texto(tela, self.transicao, (640, 125), 30, (255, 246, 218), True, True)


class ResultadoCena(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        self._resultado_enviado = None
        self.enviado = False
        self.resposta = None

    def entrar(self):
        resultado = getattr(self.jogo, "resultado_final", None) or {}
        if resultado and resultado is not self._resultado_enviado:
            self.resposta = ClienteDjango().enviar_resultado(
                resultado.get("nome", getattr(self.jogo, "nome_jogador", "Jogador")),
                resultado.get("pontos", 0),
                resultado.get("mortes", 0),
                resultado.get("tempo", 0),
            )
            self._resultado_enviado = resultado
        self.enviado = True
        self.voltar = Botao(self._tela(), "Voltar ao menu", 490, 540, 25, (53, 104, 165), COR_TEXTO, 300, 52)

    def atualizar(self, dt, teclas, eventos):
        del dt, teclas
        if self.voltar.get_click(eventos) or any(
            e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE) for e in eventos
        ):
            return "menu"
        return None

    def desenhar(self, tela=None):
        tela = self._tela(tela)
        if tela is None:
            return
        _fundo_menu(tela)
        dados = getattr(self.jogo, "resultado_final", None) or {}
        _texto(tela, "VOCÊ CHEGOU EM CASA!", (640, 112), 44, (255, 246, 218), True, True)
        _texto(tela, f"Pontuação total: {dados.get('pontos', 0)}", (640, 230), 32, (255, 214, 111), True, True)
        _texto(tela, f"Mortes: {dados.get('mortes', 0)}", (640, 288), 24, COR_TEXTO, True)
        _texto(tela, f"Tempo total: {dados.get('tempo', 0):.1f}s", (640, 330), 24, COR_TEXTO, True)
        online = bool(self.resposta and self.resposta.get("servidor"))
        status = "Resultado enviado ao Django" if online else "Modo offline: salvo localmente"
        _texto(tela, status, (640, 410), 22, (156, 220, 165) if online else (255, 208, 125), True)
        self.voltar.desenhar(tela)


class RankingCena(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        self.cliente = ClienteDjango()
        self.ranking = []
        self.voltar = None

    def entrar(self):
        self.ranking = self.cliente.obter_ranking(10)
        self.voltar = Botao(self._tela(), "Voltar ao menu", 490, 635, 22, (53, 104, 165), COR_TEXTO, 300, 46)

    def atualizar(self, dt, teclas, eventos):
        del dt, teclas
        if self.voltar and (self.voltar.get_click(eventos) or any(
            e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN) for e in eventos
        )):
            return "menu"
        return None

    def desenhar(self, tela=None):
        tela = self._tela(tela)
        if tela is None:
            return
        _fundo_menu(tela)
        _texto(tela, "RANKING • TOP 10", (640, 72), 42, (255, 246, 218), True, True)
        _texto(tela, "Pontuação ↓  •  mortes ↑  •  tempo ↑", (640, 116), 18, (205, 220, 235), True)
        if not self.ranking:
            _texto(tela, "Ainda não há resultados registrados.", (640, 260), 24, COR_TEXTO, True)
        else:
            y = 170
            for indice, entrada in enumerate(self.ranking[:10], 1):
                nome = entrada.get("nome", entrada.get("jogador", "Jogador"))
                pontos = int(entrada.get("pontuacao", entrada.get("pontuacao_total", 0)))
                mortes = int(entrada.get("mortes", 0))
                tempo = float(entrada.get("tempo", 0))
                cor = (255, 214, 111) if indice == 1 else COR_TEXTO
                _texto(tela, f"{indice:02d}", (220, y), 24, cor, False, True)
                _texto(tela, str(nome)[:20], (285, y), 24, cor, False, indice == 1)
                _texto(tela, f"{pontos:>5} pts", (690, y), 22, cor, False, indice == 1)
                _texto(tela, f"{mortes} mortes  •  {tempo:.1f}s", (860, y), 20, (205, 220, 235))
                y += 39
        if self.voltar:
            self.voltar.desenhar(tela)


class Jogo:
    """Estado compartilhado e registro de cenas do cliente Pygame."""

    def __init__(self, tela=None):
        self.tela = tela
        self.nome_jogador = ""
        self.pontuacao = None
        self.tempo = None
        self.resultado_final = None
        self.jogo_cena = JogoCena(self)
        self.cenas = {
            "menu": MenuCena(self),
            "instrucoes": InstrucoesCena(self),
            "identificacao": IdentificacaoCena(self),
            "jogo": self.jogo_cena,
            "resultado": ResultadoCena(self),
            "ranking": RankingCena(self),
        }
        self.cena_atual = "menu"
        self.cenas[self.cena_atual].entrar()

    def iniciar_partida(self, nome):
        self.nome_jogador = str(nome).strip()[:20] or "Jogador"
        self.resultado_final = None
        self.jogo_cena.iniciar(self.nome_jogador)

    def finalizar_partida(self, pontuacao, tempo):
        tempo_total = tempo.tempo_total() if hasattr(tempo, "tempo_total") else float(tempo or 0)
        self.resultado_final = {
            "nome": self.nome_jogador,
            "pontos": int(getattr(pontuacao, "pontos", pontuacao or 0)),
            "mortes": int(getattr(pontuacao, "total_mortes", 0)),
            "tempo": float(tempo_total),
        }
        self.pontuacao = pontuacao
        self.tempo = tempo

    def reiniciar_partida(self):
        self.iniciar_partida(self.nome_jogador or "Jogador")

    def trocar_cena(self, nome):
        if nome == "sair":
            return False
        if nome not in self.cenas:
            return True
        self.cena_atual = nome
        self.cenas[nome].entrar()
        return True


def _fundo_menu(tela):
    for y in range(ALTURA):
        proporcao = y / ALTURA
        cor = tuple(int(COR_CEU_1[i] * (1 - proporcao) + COR_FUNDO[i] * proporcao) for i in range(3))
        pygame.draw.line(tela, cor, (0, y), (LARGURA, y))
    pygame.draw.circle(tela, (255, 219, 135), (1090, 120), 55)
    pygame.draw.polygon(tela, (38, 61, 74), [(0, 570), (230, 420), (470, 570)])
    pygame.draw.polygon(tela, (30, 48, 64), [(300, 570), (650, 375), (1020, 570)])
    pygame.draw.rect(tela, (34, 48, 61), (0, 570, LARGURA, 150))
