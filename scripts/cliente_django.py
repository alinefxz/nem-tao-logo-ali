"""Cliente HTTP do ranking, com fallback local transparente para o jogo."""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime

from scripts.config import BASE_DIR


ARQUIVO_LOCAL = os.path.join(BASE_DIR, "offline_ranking.json")
BASE_URL = os.environ.get("NEM_TAO_LOGO_SERVER", "http://127.0.0.1:8000")


class ClienteDjango:
    def __init__(self):
        self.offline = False

    def _requisicao(self, rota, dados=None):
        url = BASE_URL.rstrip("/") + rota
        if dados is None:
            requisicao = urllib.request.Request(url, method="GET")
        else:
            corpo = json.dumps(dados).encode("utf-8")
            requisicao = urllib.request.Request(
                url,
                data=corpo,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        with urllib.request.urlopen(requisicao, timeout=3) as resposta:
            if getattr(resposta, "status", 200) >= 400:
                raise urllib.error.HTTPError(url, resposta.status, "erro HTTP", None, None)
            return json.loads(resposta.read().decode("utf-8"))

    def conectado(self):
        try:
            resposta = self._requisicao("/api/ranking/?limite=1")
            if not isinstance(resposta, dict) or not isinstance(resposta.get("ranking"), list):
                raise ValueError("resposta de ranking inválida")
            self.offline = False
            return True
        except (urllib.error.URLError, OSError, ValueError, TypeError, json.JSONDecodeError):
            self.offline = True
            return False

    def enviar_resultado(self, nome, pontuacao, mortes, tempo):
        dados = {
            "nome": str(nome).strip()[:20] or "Anônimo",
            "pontuacao": max(0, self._inteiro(pontuacao)),
            "mortes": max(0, self._inteiro(mortes)),
            "tempo": max(0.0, self._decimal(tempo)),
        }
        try:
            resposta = self._requisicao("/api/resultados/", dados)
            if not isinstance(resposta, dict) or not resposta.get("ok"):
                raise ValueError("resposta de resultado inválida")
            self.offline = False
            return {"ok": True, "servidor": True, "posicao": resposta.get("posicao")}
        except (urllib.error.URLError, OSError, ValueError, TypeError, json.JSONDecodeError):
            self.offline = True
            self._guardar_local(dados)
            return {"ok": True, "servidor": False, "posicao": None}

    def obter_ranking(self, limite=10):
        limite = max(1, min(50, self._inteiro(limite, 10)))
        try:
            resposta = self._requisicao(f"/api/ranking/?limite={limite}")
            if not isinstance(resposta, dict) or not isinstance(resposta.get("ranking"), list):
                raise ValueError("resposta de ranking inválida")
            self.offline = False
            return self._ordenar(resposta["ranking"])[:limite]
        except (urllib.error.URLError, OSError, ValueError, TypeError, json.JSONDecodeError):
            self.offline = True
            return self._ranking_local()[:limite]

    def _guardar_local(self, dados):
        entrada = {
            "nome": dados["nome"],
            "pontuacao": dados["pontuacao"],
            "mortes": dados["mortes"],
            "tempo": dados["tempo"],
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        entradas = self._ranking_local()
        entradas.append(entrada)
        try:
            with open(ARQUIVO_LOCAL, "w", encoding="utf-8") as arquivo:
                json.dump(self._ordenar(entradas), arquivo, ensure_ascii=False, indent=2)
        except OSError:
            # O jogo continua jogável mesmo que o diretório local seja somente leitura.
            pass

    def _ranking_local(self):
        if not os.path.exists(ARQUIVO_LOCAL):
            return []
        try:
            with open(ARQUIVO_LOCAL, encoding="utf-8") as arquivo:
                entrada = json.load(arquivo)
            if not isinstance(entrada, list):
                return []
            return self._ordenar(entrada)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []

    @staticmethod
    def _inteiro(valor, padrao=0):
        try:
            return int(valor)
        except (TypeError, ValueError, OverflowError):
            return padrao

    @staticmethod
    def _decimal(valor, padrao=0.0):
        try:
            return float(valor)
        except (TypeError, ValueError, OverflowError):
            return padrao

    @classmethod
    def _ordenar(cls, entradas):
        melhores = {}
        for entrada in entradas:
            if not isinstance(entrada, dict):
                continue
            nome = str(entrada.get("nome", entrada.get("jogador", "Anônimo"))).strip()[:20] or "Anônimo"
            item = {
                "nome": nome,
                "pontuacao": max(0, cls._inteiro(entrada.get("pontuacao", entrada.get("pontuacao_total", 0)))),
                "mortes": max(0, cls._inteiro(entrada.get("mortes", 0))),
                "tempo": max(0.0, cls._decimal(entrada.get("tempo", 0))),
                "data": entrada.get("data", ""),
            }
            anterior = melhores.get(nome)
            if anterior is None or cls._chave_ordenacao(item) < cls._chave_ordenacao(anterior):
                melhores[nome] = item
        ordenadas = sorted(melhores.values(), key=cls._chave_ordenacao)
        for posicao, item in enumerate(ordenadas, 1):
            item["posicao"] = posicao
        return ordenadas

    @staticmethod
    def _chave_ordenacao(entrada):
        return (-entrada["pontuacao"], entrada["mortes"], entrada["tempo"], entrada.get("data", ""))
