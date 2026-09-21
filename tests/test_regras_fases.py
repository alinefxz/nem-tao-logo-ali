import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from scripts.config import NOMES_FASES
from scripts.fases_planos import contruir_plano
from scripts.pontuacao import GerenciadorPontuacao


class TestRegrasFases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_death_penalty_never_makes_score_negative(self):
        score = GerenciadorPontuacao()
        score.registrar_morte()
        self.assertEqual(score.pontos, 0)

    def test_each_phase_has_expected_name_and_order(self):
        self.assertEqual(
            [contruir_plano(i)["nome"] for i in range(5)],
            list(NOMES_FASES),
        )

    def test_checkpoint_bonus_is_awarded_once(self):
        score = GerenciadorPontuacao()
        self.assertTrue(score.checkpoint(False))
        self.assertEqual(score.pontos, 50)
        self.assertFalse(score.checkpoint(True))
        self.assertEqual(score.pontos, 50)

    def test_invalid_phase_index_is_rejected(self):
        with self.assertRaises(ValueError):
            contruir_plano(5)


if __name__ == "__main__":
    unittest.main()
