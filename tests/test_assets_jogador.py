import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from scripts.assets import carregar_animacao
from scripts.config import CHAO_Y
from scripts.interfaces import Botao
from scripts.jogador import Jogador


class TestAssetsJogador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_frames_are_sorted_by_numeric_suffix_and_share_canvas(self):
        frames = carregar_animacao("personagem", "parada", 88)
        self.assertGreaterEqual(len(frames), 2)
        self.assertEqual(len({frame.get_size() for frame in frames}), 1)

    def test_player_constructor_matches_phase_api(self):
        jogador = Jogador(100, 600)
        self.assertEqual(jogador.rect.bottom, 600)
        self.assertGreater(jogador.rect.width, 0)

    def test_player_uses_idle_and_burrow_animation_states(self):
        jogador = Jogador(100, CHAO_Y)
        self.assertIn("parada", jogador.animacoes)
        self.assertIn("buraco", jogador.animacoes)
        jogador.mover(0)
        jogador.atualizar(1 / 60, [], [])
        self.assertEqual(jogador.estado, "parada")
        jogador.iniciar_queda_buraco()
        self.assertEqual(jogador.estado, "buraco")

    def test_player_keeps_running_animation_when_shift_is_held(self):
        jogador = Jogador(100, CHAO_Y)
        jogador.mover(1, correndo=True)
        jogador.atualizar(1 / 60, [], [])
        self.assertEqual(jogador.estado, "correr")

        jogador.mover(1, correndo=False)
        jogador.atualizar(1 / 60, [], [])
        self.assertEqual(jogador.estado, "andar")

    def test_button_uses_click_event(self):
        surface = pygame.Surface((100, 60))
        button = Botao(surface, "Jogar", 10, 10, 24, (20, 20, 20), (255, 255, 255))
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(20, 20), button=1)
        self.assertTrue(button.get_click([event]))


if __name__ == "__main__":
    unittest.main()
