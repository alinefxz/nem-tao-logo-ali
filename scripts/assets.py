import os
import re

import pygame

from scripts.config import ALTURA_JOGADOR, ASSETS_DIR


CACHE = {}
_ANIMATION_RE = re.compile(r"^(?P<nome>.+)-(?P<indice>\d+)\.png$", re.IGNORECASE)


def caminho_asset(*partes):
    return os.path.join(ASSETS_DIR, *partes)


def _imagem_com_alpha(caminho):
    if caminho in CACHE:
        return CACHE[caminho]
    imagem = pygame.image.load(caminho)
    if pygame.display.get_init() and pygame.display.get_surface() is not None:
        imagem = imagem.convert_alpha()
    else:
        imagem = imagem.convert_alpha() if imagem.get_alpha() is not None else imagem.convert()
    CACHE[caminho] = imagem
    return imagem


def _arquivos_animacao(diretorio, nome):
    arquivos = []
    for arquivo in os.listdir(diretorio):
        correspondencia = _ANIMATION_RE.match(arquivo)
        if correspondencia and correspondencia.group("nome") == nome:
            arquivos.append((int(correspondencia.group("indice")), arquivo))
    return [arquivo for _, arquivo in sorted(arquivos, key=lambda item: item[0])]


def _recortar_alpha(imagem):
    if imagem.get_masks()[3] == 0:
        return imagem.copy()
    limites = imagem.get_bounding_rect(min_alpha=1)
    if limites.width == 0 or limites.height == 0:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    return imagem.subsurface(limites).copy()


def normalizar_frame(imagem, altura, largura_canvas=None):
    """Recorta a transparência e ancora o conteúdo pelo centro e pela base."""
    recortada = _recortar_alpha(imagem)
    escala = altura / max(1, recortada.get_height())
    largura = max(1, round(recortada.get_width() * escala))
    redimensionada = pygame.transform.smoothscale(recortada, (largura, altura))
    largura_canvas = max(largura, largura_canvas or largura)
    canvas = pygame.Surface((largura_canvas, altura), pygame.SRCALPHA)
    canvas.blit(redimensionada, ((largura_canvas - largura) // 2, altura - redimensionada.get_height()))
    return canvas


def altura_referencia_animacao(pasta, nome):
    """Retorna a altura real de referência de uma animação.

    Alguns sprites possuem elementos de cenário no quadro (por exemplo, a
    animação de queda no bueiro). Para manter a escala desses elementos, é
    melhor usar a altura de uma pose de personagem como referência do que
    redimensionar cada quadro isoladamente.
    """
    diretorio = os.path.join(ASSETS_DIR, pasta)
    arquivos = _arquivos_animacao(diretorio, nome) if os.path.isdir(diretorio) else []
    if not arquivos:
        return 1
    alturas = []
    for arquivo in arquivos:
        imagem = _imagem_com_alpha(os.path.join(diretorio, arquivo))
        alturas.append(_recortar_alpha(imagem).get_height())
    return max(1, max(alturas))


def carregar_animacao(pasta, nome, altura, n_frames=None, altura_referencia=None):
    diretorio = os.path.join(ASSETS_DIR, pasta)
    arquivos = _arquivos_animacao(diretorio, nome) if os.path.isdir(diretorio) else []
    if n_frames is not None:
        arquivos = arquivos[:n_frames]
    imagens = [_imagem_com_alpha(os.path.join(diretorio, arquivo)) for arquivo in arquivos]
    if not imagens:
        return [_caixa_fallback(nome, altura)]

    recortadas = [_recortar_alpha(imagem) for imagem in imagens]

    if altura_referencia is not None:
        # Mantém uma escala única para todos os quadros. Isso é importante
        # para animações que misturam personagem e cenário, como ``buraco``:
        # o quadro do bueiro vazio não pode aumentar de tamanho sozinho.
        escala = altura / max(1, altura_referencia)
        tamanhos = [
            (
                max(1, round(imagem.get_width() * escala)),
                max(1, round(imagem.get_height() * escala)),
            )
            for imagem in recortadas
        ]
        largura_canvas = max(largura for largura, _ in tamanhos)
        altura_canvas = max(altura, max(altura_quadro for _, altura_quadro in tamanhos))
        quadros = []
        for imagem, tamanho in zip(recortadas, tamanhos):
            redimensionada = pygame.transform.smoothscale(imagem, tamanho)
            canvas = pygame.Surface((largura_canvas, altura_canvas), pygame.SRCALPHA)
            canvas.blit(redimensionada, ((largura_canvas - tamanho[0]) // 2, altura_canvas - tamanho[1]))
            quadros.append(canvas)
        return quadros

    larguras = [max(1, round(imagem.get_width() * altura / max(1, imagem.get_height()))) for imagem in recortadas]
    largura_canvas = max(larguras)
    return [normalizar_frame(imagem, altura, largura_canvas) for imagem in recortadas]


def _caixa_fallback(nome, altura):
    superficie = pygame.Surface((max(1, int(altura * 0.6)), altura), pygame.SRCALPHA)
    cor = (200, 120, 80, 255) if nome != "porta" else (120, 70, 50, 255)
    superficie.fill(cor)
    return superficie


def carregar_imagem(pasta, nome, altura=0, largura=0):
    diretorio = os.path.join(ASSETS_DIR, pasta)
    caminho = os.path.join(diretorio, nome)
    if not os.path.exists(caminho):
        candidatos = [arquivo for arquivo in os.listdir(diretorio) if arquivo.startswith(nome.split("-")[0])]
        if not candidatos:
            return _caixa_fallback(nome, altura or 64)
        caminho = os.path.join(diretorio, sorted(candidatos)[0])
    imagem = _imagem_com_alpha(caminho)
    if altura:
        escala = altura / max(1, imagem.get_height())
        largura = largura or max(1, round(imagem.get_width() * escala))
        imagem = pygame.transform.smoothscale(imagem, (largura, altura))
    elif largura:
        escala = largura / max(1, imagem.get_width())
        imagem = pygame.transform.smoothscale(imagem, (largura, max(1, round(imagem.get_height() * escala))))
    return imagem


def encontrar_calcada():
    diretorio = os.path.join(ASSETS_DIR, "cenario")
    if not os.path.isdir(diretorio):
        return None
    for arquivo in os.listdir(diretorio):
        if arquivo.lower().startswith("cal") and "falsa" not in arquivo.lower():
            return os.path.join(diretorio, arquivo)
    return None


def carregar_calcada():
    caminho = encontrar_calcada()
    if caminho is None:
        return None
    if caminho in CACHE:
        return CACHE[caminho]
    imagem = _imagem_com_alpha(caminho)
    imagem = _recortar_fundo_escuro(imagem)
    CACHE[caminho] = imagem
    return imagem


def _recortar_fundo_escuro(imagem, limiar=18):
    """Remove o fundo preto do PNG da calçada e conserva a arte do piso.

    Esse asset foi exportado com fundo preto opaco, não com transparência.
    Uma máscara por limiar remove somente as áreas escuras conectadas ao
    fundo visual e permite recortar a faixa real antes de redimensioná-la.
    """
    mascara = pygame.mask.from_threshold(
        imagem,
        (0, 0, 0),
        (limiar, limiar, limiar, 255),
    )
    mascara.invert()
    alpha = mascara.to_surface(
        setcolor=(255, 255, 255, 255),
        unsetcolor=(0, 0, 0, 0),
    )
    limites = alpha.get_bounding_rect()
    if limites.width == 0 or limites.height == 0:
        return imagem.copy()
    recortada = pygame.Surface(imagem.get_size(), pygame.SRCALPHA)
    recortada.blit(imagem, (0, 0))
    recortada.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return recortada.subsurface(limites).copy()


def pre_carregar():
    carregar_calcada()
    for nome in (
        "parada",
        "andar",
        "correr",
        "pular",
        "cair",
        "aterrissando",
        "buraco",
        "abaixar",
        "derrapando",
        "agua",
        "morrendo",
        "respawn",
        "porta",
    ):
        carregar_animacao("personagem", nome, ALTURA_JOGADOR)
