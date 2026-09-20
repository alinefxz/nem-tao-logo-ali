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


def carregar_animacao(pasta, nome, altura, n_frames=None):
    diretorio = os.path.join(ASSETS_DIR, pasta)
    arquivos = _arquivos_animacao(diretorio, nome) if os.path.isdir(diretorio) else []
    if n_frames is not None:
        arquivos = arquivos[:n_frames]
    imagens = [_imagem_com_alpha(os.path.join(diretorio, arquivo)) for arquivo in arquivos]
    if not imagens:
        return [_caixa_fallback(nome, altura)]

    recortadas = [_recortar_alpha(imagem) for imagem in imagens]
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
    CACHE[caminho] = imagem
    return imagem


def pre_carregar():
    carregar_calcada()
    for nome in ("parada", "correr", "pular", "cair", "aterrissando", "morrendo", "respawn", "buraco", "derrapando", "porta"):
        carregar_animacao("personagem", nome, ALTURA_JOGADOR)
