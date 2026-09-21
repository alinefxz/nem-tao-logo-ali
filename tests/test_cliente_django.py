import json
import os
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from scripts import cliente_django


class TestClienteDjango(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.arquivo = os.path.join(self.temp_dir.name, "ranking.json")
        self.patch_arquivo = patch.object(cliente_django, "ARQUIVO_LOCAL", self.arquivo)
        self.patch_arquivo.start()

    def tearDown(self):
        self.patch_arquivo.stop()
        self.temp_dir.cleanup()

    def test_envio_offline_salva_e_nao_quebra(self):
        cliente = cliente_django.ClienteDjango()
        with patch.object(cliente, "_requisicao", side_effect=urllib.error.URLError("offline")):
            resposta = cliente.enviar_resultado("  Ali  ", -4, -1, -2)
        self.assertEqual(resposta["servidor"], False)
        with open(self.arquivo, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        self.assertEqual(dados[0]["nome"], "Ali")
        self.assertEqual(dados[0]["pontuacao"], 0)

    def test_ranking_offline_e_unico_e_ordenado(self):
        with open(self.arquivo, "w", encoding="utf-8") as arquivo:
            json.dump(
                [
                    {"nome": "Bia", "pontuacao": 400, "mortes": 0, "tempo": 2},
                    {"nome": "Ali", "pontuacao": 900, "mortes": 2, "tempo": 9},
                    {"nome": "Ali", "pontuacao": 950, "mortes": 1, "tempo": 12},
                ],
                arquivo,
            )
        cliente = cliente_django.ClienteDjango()
        with patch.object(cliente, "_requisicao", side_effect=urllib.error.URLError("offline")):
            ranking = cliente.obter_ranking(10)
        self.assertEqual([entrada["nome"] for entrada in ranking], ["Ali", "Bia"])
        self.assertEqual(ranking[0]["pontuacao"], 950)


if __name__ == "__main__":
    unittest.main()
