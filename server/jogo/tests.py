import json

from django.test import TestCase

from .models import Jogador, Resultado


class ResultadoApiTests(TestCase):
    def test_post_resultado_cria_jogador_e_normaliza_negativos(self):
        response = self.client.post(
            "/api/resultados/",
            data=json.dumps({"nome": "  Ali  ", "pontuacao": -5, "mortes": -2, "tempo": -1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        resultado = Resultado.objects.get()
        self.assertEqual(resultado.jogador.nome, "Ali")
        self.assertEqual(resultado.pontuacao, 0)
        self.assertEqual(resultado.mortes, 0)
        self.assertEqual(resultado.tempo, 0)

    def test_post_rejeita_json_que_nao_e_objeto(self):
        response = self.client.post(
            "/api/resultados/", data=json.dumps(["Ali"]), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_ranking_e_unico_por_jogador_e_respeita_limite(self):
        jogador = Jogador.objects.create(nome="Ali")
        Resultado.objects.create(jogador=jogador, pontuacao=400, mortes=2, tempo=10)
        Resultado.objects.create(jogador=jogador, pontuacao=900, mortes=1, tempo=20)
        for indice in range(12):
            outro = Jogador.objects.create(nome=f"J{indice:02d}")
            Resultado.objects.create(jogador=outro, pontuacao=800 - indice)

        response = self.client.get("/api/ranking/?limite=10")
        self.assertEqual(response.status_code, 200)
        ranking = response.json()["ranking"]
        self.assertEqual(len(ranking), 10)
        self.assertEqual(len({item["nome"] for item in ranking}), 10)
        self.assertEqual(ranking[0]["nome"], "Ali")

    def test_ranking_limita_valor_maximo(self):
        response = self.client.get("/api/ranking/?limite=999")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()["ranking"]), 50)
