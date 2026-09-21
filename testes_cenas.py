import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.assets import pre_carregar
from scripts.cenas import (
    IdentificacaoCena,
    InstrucoesCena,
    JogoCena,
    MenuCena,
    RankingCena,
    ResultadoCena,
)
from scripts.config import ALTURA, LARGURA


class Teclas:
    def __init__(self, d=1):
        self.d = d

    def __getitem__(self, k):
        if k in (pygame.K_a, pygame.K_LEFT):
            return self.d < 0
        if k in (pygame.K_d, pygame.K_RIGHT):
            return self.d > 0
        return False


class StubJogo:
    def __init__(self):
        self.ultimo_nome = ""
        self.resultado_final = None
        self.jogo_cena = None

    def iniciar_partida(self, nome):
        self.ultimo_nome = nome
        self.resultado_final = None
        self.jogo_cena.iniciar(nome)

    def finalizar_partida(self, pont, tempo):
        self.resultado_final = {
            "pontos": pont.pontos,
            "mortes": pont.total_mortes,
            "tempo": tempo.tempo_total(),
        }


def evento_tecla(tipo, chave, unicode=""):
    e = pygame.event.Event(tipo, key=chave, unicode=unicode)
    return e


def main():
    pygame.init()
    pygame.display.set_caption("teste")
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pre_carregar()

    jogo = StubJogo()
    menu = MenuCena(jogo)
    instrucoes = InstrucoesCena(jogo)
    identificacao = IdentificacaoCena(jogo)
    ranking = RankingCena(jogo)
    jogo_cena = JogoCena(jogo)
    resultado = ResultadoCena(jogo)
    jogo.jogo_cena = jogo_cena

    menu.entrar()
    menu.atualizar(1 / 60, Teclas(), [])
    menu.desenhar(tela)

    instrucoes.entrar()
    instrucoes.atualizar(1 / 60, Teclas(), [])
    instrucoes.desenhar(tela)

    identificacao.entrar()
    eventos = [
        evento_tecla(pygame.KEYDOWN, pygame.K_a, "A"),
        evento_tecla(pygame.KEYDOWN, pygame.K_l, "l"),
        evento_tecla(pygame.KEYDOWN, pygame.K_i, "i"),
    ]
    identificacao.atualizar(1 / 60, Teclas(), eventos)
    assert identificacao.nome == "Ali"
    assert identificacao._confirmar() == "jogo"
    identificacao.desenhar(tela)

    ranking.entrar()
    ranking.desenhar(tela)
    assert ranking.atualizar(1 / 60, Teclas(), [evento_tecla(pygame.KEYDOWN, pygame.K_RETURN)]) == "menu"

    dt = 1 / 30
    total_ticks = 0
    resultado_fluxo = None
    while resultado_fluxo is None and total_ticks < 24000:
        total_ticks += 1
        fase = jogo_cena.fase
        if fase is not None and not fase.concluida:
            porta_x = fase.plano["porta"]
            fase.jogador.x = porta_x - 50
            fase.jogador.y = fase.jogador.chao_y
            fase.jogador.vy = 0.0
        resultado_fluxo = jogo_cena.atualizar(dt, Teclas(), [])
        if jogo_cena.transicao is not None:
            jogo_cena.desenhar(tela)
    assert resultado_fluxo == "resultado", f"fluxo retornou {resultado_fluxo}"
    jogo_cena.desenhar(tela)

    resultado.entrar()
    assert resultado.enviado is True
    resultado.desenhar(tela)

    esc = evento_tecla(pygame.KEYDOWN, pygame.K_ESCAPE)
    jogo_cena.fase = None
    assert jogo_cena.atualizar(1 / 60, Teclas(), []) == "menu"

    print("CENAS: OK")
    pygame.quit()


if __name__ == "__main__":
    main()