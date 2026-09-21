import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

LARGURA, ALTURA = 1280, 720
FPS = 60

COR_CEU_1 = (105, 175, 235)
COR_CEU_2 = (190, 225, 250)
COR_FUNDO = (60, 80, 120)
COR_TERRA = (120, 90, 70)
COR_TEXTO = (255, 255, 255)
COR_TEXTO_ESCURO = (30, 30, 30)
COR_BORDA_BOTAO = (255, 255, 255)
COR_CASA = (150, 60, 40)
COR_ARVORE = (45, 110, 55)
COR_ASFALTO = (55, 58, 64)

CIMA = (0.0, 1.0)
GRAVIDADE = 2300.0
VEL_PULO = -820.0
VEL_ANDAR = 220.0
VEL_CORRIDA = 330.0
VEL_DERRAPAGEM = 540.0
TEMPO_RESPAWN = 1.25

# O personagem anda sobre o topo da calçada; a rua fica acima dela.
CHAO_Y = 662
ALTURA_RUA = 62
LARGURA_JOGADOR = 34
ALTURA_JOGADOR = 88

TEMPO_REFERENCIA = (95, 95, 100, 105, 110)
BONUS_FASE = 300
BONUS_SEM_MORTES = 150
BONUS_CHECKPOINT = 50
PENALIDADE_MORTE = 25
BONUS_TEMPO_MAX = 200

NOMES_FASES = [
    "A Rua",
    "Em Obras",
    "A Avenida",
    "O Atalho",
    "O Último Quarteirão",
]
