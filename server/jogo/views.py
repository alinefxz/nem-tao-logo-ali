import json

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Jogador, Resultado


def inicio(request):
    return HttpResponse(
        "<h1>Nem Tão Logo Ali - servidor</h1>"
        "<p>Servidor da casa funcionando. Para jogar, rode <code>python main.py</code>.</p>"
        "<ul>"
        "<li><a href=\"/api/ranking/\">/api/ranking/</a> - ranking das 10 melhores pontuações</li>"
        "<li><code>POST /api/resultados/</code> - registrar um resultado</li>"
        "<li><a href=\"/admin/\">/admin/</a> - painel de administração</li>"
        "</ul>"
    )


def _inteiro(valor, padrao=0):
    try:
        return int(valor)
    except (TypeError, ValueError, OverflowError):
        return padrao


def _decimal(valor, padrao=0.0):
    try:
        return float(valor)
    except (TypeError, ValueError, OverflowError):
        return padrao


def _formato(entrada, posicao=None):
    item = {
        "nome": entrada.jogador.nome,
        "pontuacao": entrada.pontuacao,
        "mortes": entrada.mortes,
        "tempo": round(entrada.tempo, 2),
        "data": timezone.localtime(entrada.data).strftime("%d/%m/%Y %H:%M"),
    }
    if posicao is not None:
        item["posicao"] = posicao
    return item


def _melhores_por_jogador():
    melhores = {}
    entradas = Resultado.objects.select_related("jogador").order_by(
        "-pontuacao", "mortes", "tempo", "data", "id"
    )
    for entrada in entradas:
        melhores.setdefault(entrada.jogador_id, entrada)
    return sorted(
        melhores.values(),
        key=lambda entrada: (-entrada.pontuacao, entrada.mortes, entrada.tempo, entrada.data, entrada.id),
    )


@csrf_exempt
def resultados(request):
    if request.method != "POST":
        return JsonResponse({"erro": "método não permitido"}, status=405)
    try:
        dados = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"erro": "corpo inválido"}, status=400)
    if not isinstance(dados, dict):
        return JsonResponse({"erro": "o corpo deve ser um objeto JSON"}, status=400)

    nome = str(dados.get("nome", "")).strip()[:20] or "Anônimo"
    pontuacao = max(0, _inteiro(dados.get("pontuacao", 0)))
    mortes = max(0, _inteiro(dados.get("mortes", 0)))
    tempo = max(0.0, _decimal(dados.get("tempo", 0)))

    jogador, _ = Jogador.objects.get_or_create(nome=nome)
    resultado = Resultado.objects.create(
        jogador=jogador, pontuacao=pontuacao, mortes=mortes, tempo=tempo
    )
    melhores = _melhores_por_jogador()
    posicao = next(
        (indice for indice, entrada in enumerate(melhores, 1) if entrada.jogador_id == jogador.id),
        len(melhores) + 1,
    )
    return JsonResponse({"ok": True, "id": resultado.id, "posicao": posicao})


def ranking(request):
    limite = max(1, min(50, _inteiro(request.GET.get("limite", 10), 10)))
    corpo = [
        _formato(entrada, posicao)
        for posicao, entrada in enumerate(_melhores_por_jogador()[:limite], 1)
    ]
    return JsonResponse({"ranking": corpo})
