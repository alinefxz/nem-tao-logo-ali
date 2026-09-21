from scripts.obstaculos import (
    BarreiraTemporizada,
    Buraco,
    BuracoMovel,
    CalcadaFalsa,
    Carro,
    CheckpointObjeto,
    ConeRolante,
    ConesDeslizam,
    GalhoCaindo,
    Pendulo,
    PlacaGiratoria,
    PlacaQueCai,
    PlataformaAfastada,
    PocaEscorregadia,
    Porta,
    Semaforo,
    TrianguloFixo,
)


def _plano_base(nome, largura, spawn, porta, checkpoint=None):
    return {
        "nome": nome,
        "largura": largura,
        "spawn": spawn,
        "porta": porta,
        "checkpoint": checkpoint,
        "buracos": [],
        "buraco_moveis": [],
        "obstaculos": [],
    }


def _plano_1():
    plano = _plano_base("A Rua", 3400, 150, 3220)
    plano["buracos"] = [(950, 160)]
    plano["buraco_moveis"] = [(1650, 1880, 150, 170)]
    plano["obstaculos"] = [
        CalcadaFalsa(2850, 190),
        PlacaQueCai(2300),
        ConeRolante(2050, velocidade=230, limites=(1985, 2100)),
        Buraco(2850, 190),
        TrianguloFixo(700),
        TrianguloFixo(2550),
    ]
    return plano


def _plano_2():
    plano = _plano_base("Em Obras", 4000, 150, 3820, checkpoint=2450)
    plano["buracos"] = [(600, 150)]
    plano["buraco_moveis"] = [(1600, 1820, 160, 150)]
    plano["obstaculos"] = [
        BarreiraTemporizada(950, periodo_baixo=1.5, periodo_alto=1.5),
        ConesDeslizam(1250, 1450, velocidade=170),
        CalcadaFalsa(2000, 220),
        Buraco(2000, 220),
        CalcadaFalsa(2300, 220),
        Buraco(2300, 220),
        Carro(2900, velocidade=300, sentido=-1, sprite="carro", largura=230, altura=115),
        Buraco(3350, 160),
        TrianguloFixo(2700),
    ]
    return plano


def _plano_3():
    plano = _plano_base("A Avenida", 4400, 150, 4220, checkpoint=2600)
    plano["buracos"] = [(3600, 160)]
    plano["obstaculos"] = [
        Semaforo(1750, periodo_verde=2.6, periodo_vermelho=1.6),
        Carro(1500, velocidade=250, sentido=-1, sprite="carro", largura=230, altura=115),
        Carro(2000, velocidade=300, sentido=1, sprite="azul", largura=105, altura=90),
        Carro(2400, velocidade=400, sentido=-1, sprite="azulr", largura=100, altura=110, acelerado=True),
        PocaEscorregadia(3000, largura=170),
        PlacaGiratoria(3400, periodo=2.4),
        Carro(3850, velocidade=330, sentido=-1, sprite="azul", largura=105, altura=90),
        TrianguloFixo(600),
        TrianguloFixo(700),
    ]
    return plano


def _plano_4():
    plano = _plano_base("O Atalho", 4600, 150, 4420, checkpoint=2300)
    plano["buracos"] = [(1500, 260), (2200, 200), (3450, 200)]
    plano["obstaculos"] = [
        GalhoCaindo(800, intervalo=2.6),
        Pendulo(1250, comprimento=200, amplitude=0.95, periodo=2.4),
        PlataformaAfastada(1500, largura=280, distancia=420, gatilho_dist=360),
        GalhoCaindo(2100, intervalo=1.9),
        CalcadaFalsa(2650, 210),
        Buraco(2650, 210),
        Pendulo(2900, comprimento=210, amplitude=1.0, periodo=2.1),
        ConeRolante(3700, velocidade=430, altura=88, limites=(3565, 3850)),
        GalhoCaindo(3800, intervalo=2.2),
    ]
    return plano


def _plano_5():
    plano = _plano_base("O Último Quarteirão", 4800, 150, 4520, checkpoint=4100)
    plano["buracos"] = [(600, 150), (3050, 220)]
    plano["buraco_moveis"] = [(1750, 1950, 160, 160)]
    plano["obstaculos"] = [
        PlacaQueCai(900),
        PlacaQueCai(1150),
        BarreiraTemporizada(1400, periodo_baixo=1.2, periodo_alto=1.2),
        GalhoCaindo(1650, intervalo=2.3),
        ConeRolante(2150, velocidade=420, limites=(2055, 2300)),
        Carro(2600, velocidade=340, sentido=-1, sprite="carro", largura=230, altura=115),
        PlacaGiratoria(2850, periodo=2.0),
        Pendulo(3300, comprimento=210, amplitude=1.0, periodo=2.0),
        CalcadaFalsa(3050, 230),
        PlataformaAfastada(3600, largura=220, distancia=380, gatilho_dist=340),
        GalhoCaindo(3950, intervalo=2.0),
        Buraco(4250, 180),
    ]
    return plano


def contruir_plano(indice):
    construtores = [_plano_1, _plano_2, _plano_3, _plano_4, _plano_5]
    if not isinstance(indice, int) or not 0 <= indice < len(construtores):
        raise ValueError(f"índice de fase inválido: {indice}")
    return construtores[indice]()


def adicionar_marcadores(plano, fase):
    if plano["checkpoint"] is not None:
        fase.obstaculos.append(CheckpointObjeto(plano["checkpoint"]))
    fase.obstaculos.append(Porta(plano["porta"]))
