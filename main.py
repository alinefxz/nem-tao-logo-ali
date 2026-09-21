"""Ponto de entrada do jogo Nem Tão Logo Ali."""

import os

os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

import pygame

from scripts.assets import pre_carregar
from scripts.cenas import Jogo
from scripts.config import FPS, ALTURA, LARGURA


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Nem Tão Logo Ali")
    pre_carregar()
    jogo = Jogo(tela)
    relogio = pygame.time.Clock()
    executando = True

    while executando:
        dt = min(relogio.tick(FPS) / 1000.0, 0.05)
        eventos = pygame.event.get()
        if any(evento.type == pygame.QUIT for evento in eventos):
            break
        teclas = pygame.key.get_pressed()
        cena = jogo.cenas[jogo.cena_atual]
        proxima = cena.atualizar(dt, teclas, eventos)
        if proxima:
            if proxima == "sair":
                break
            jogo.trocar_cena(proxima)
        tela.fill((20, 30, 45))
        jogo.cenas[jogo.cena_atual].desenhar(tela)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
