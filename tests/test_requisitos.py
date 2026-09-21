import unittest

from scripts.cliente_django import ClienteDjango
from scripts.config import (
    BONUS_CHECKPOINT,
    BONUS_FASE,
    BONUS_SEM_MORTES,
    BONUS_TEMPO_MAX,
    NOMES_FASES,
    PENALIDADE_MORTE,
)
from scripts.fases_planos import contruir_plano


class TestRequisitos(unittest.TestCase):
    def test_exatamente_cinco_planos_de_fase(self):
        self.assertEqual(len(NOMES_FASES), 5)
        self.assertEqual([contruir_plano(i)["nome"] for i in range(5)], list(NOMES_FASES))

    def test_constantes_de_pontuacao(self):
        self.assertEqual(
            (BONUS_FASE, BONUS_SEM_MORTES, BONUS_CHECKPOINT, PENALIDADE_MORTE, BONUS_TEMPO_MAX),
            (300, 150, 50, 25, 200),
        )

    def test_ranking_tem_limite_dez(self):
        self.assertLessEqual(len(ClienteDjango().obter_ranking(10)), 10)


if __name__ == "__main__":
    unittest.main()
