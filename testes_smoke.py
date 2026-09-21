import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from scripts.fase import Fase
from scripts.pontuacao import GerenciadorPontuacao
from scripts.tempo import GerenciadorTempo


class TeclasNeutras:
    def __getitem__(self, chave):
        del chave
        return False


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    pontuacao = GerenciadorPontuacao()
    tempo = GerenciadorTempo()
    for indice in range(5):
        fase = Fase(indice, pontuacao, tempo)
        fase.jogador.x = fase.porta.x - 20
        fase.jogador.y = fase.jogador.chao_y
        for _ in range(5):
            fase.atualizar(1 / 60, TeclasNeutras(), False)
            if fase.concluida:
                break
        assert fase.concluida, f"fase {indice + 1} não concluiu"
        print(f"Fase {indice + 1}: CONCLUÍDA")
    assert pontuacao.pontos >= 0
    print("SMOKE: OK")
    pygame.quit()


if __name__ == "__main__":
    main()
