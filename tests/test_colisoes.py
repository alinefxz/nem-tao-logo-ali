import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from scripts.config import ALTURA, CHAO_Y
from scripts.fase import Fase
from scripts.config import TEMPO_RESPAWN
from scripts.jogador import LARGURA_BUEIRO_ANIMACAO_MAX
from scripts.obstaculos import Buraco, BuracoMovel, ConeRolante, PlacaQueCai, TrianguloFixo


class TeclasNeutras:
    def __getitem__(self, chave):
        del chave
        return False


class TeclasDireita:
    def __getitem__(self, chave):
        return chave in (pygame.K_d, pygame.K_RIGHT)


class TestColisoesDoCenario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_post_tem_apenas_hitbox_na_base(self):
        poste = TrianguloFixo(700)
        self.assertLessEqual(poste.hitbox.bottom, CHAO_Y)
        self.assertLessEqual(poste.hitbox.height, 24)

    def test_bueiro_nao_mata_ao_encostar_com_a_lateral(self):
        fase = Fase(0)
        bueiro = fase.buracos[0]
        fase.jogador.x = bueiro.hitbox.left - 5
        fase.jogador._atualizar_rect()
        fase.atualizar(1 / 60, TeclasNeutras(), False)
        self.assertFalse(fase.jogador.caindo_no_buraco)
        self.assertFalse(fase.jogador.morto)

    def test_bueiro_inicia_queda_somente_com_os_pes_no_vazio(self):
        fase = Fase(0)
        bueiro = fase.buracos[0]
        fase.jogador.x = bueiro.hitbox.centerx
        fase.jogador._atualizar_rect()
        fase.atualizar(1 / 60, TeclasNeutras(), False)
        self.assertTrue(fase.jogador.caindo_no_buraco)
        self.assertFalse(fase.jogador.morto)

    def test_queda_no_bueiro_mantem_animacao_de_queda_ate_respawn(self):
        fase = Fase(0)
        bueiro = fase.buracos[0]
        fase.jogador.x = bueiro.hitbox.centerx
        fase.jogador._atualizar_rect()
        for _ in range(120):
            fase.atualizar(1 / 60, TeclasNeutras(), False)
            if fase.jogador.morto:
                break
        self.assertTrue(fase.jogador.morto)
        self.assertEqual(fase.jogador.estado, "buraco")

    def test_salto_nao_troca_para_animacao_de_morte(self):
        fase = Fase(0)
        fase.jogador.pular()
        fase.atualizar(1 / 60, TeclasNeutras(), False)
        self.assertFalse(fase.jogador.morto)
        self.assertEqual(fase.jogador.estado, "pular")

    def test_salto_usa_pular_ate_aterrissar(self):
        fase = Fase(0)
        fase.jogador.pular()
        viu_pulo = False
        for _ in range(90):
            fase.atualizar(1 / 60, TeclasNeutras(), False)
            if not fase.jogador.no_chao:
                viu_pulo = True
                self.assertEqual(fase.jogador.estado, "pular")
            elif viu_pulo:
                self.assertIn(fase.jogador.estado, ("aterrissando", "parada"))
                break
        self.assertTrue(viu_pulo)

    def test_salto_ultrapassa_poste_sem_morrer(self):
        fase = Fase(0)
        fase.jogador.x = 610
        fase.jogador._atualizar_rect()
        fase.jogador.pular()
        for _ in range(75):
            fase.atualizar(1 / 60, TeclasDireita(), False)
        self.assertFalse(fase.jogador.morto)
        self.assertNotEqual(fase.jogador.estado, "morrendo")

    def test_aterrissagem_usa_animacao_propria(self):
        fase = Fase(0)
        fase.jogador.pular()
        for _ in range(90):
            fase.atualizar(1 / 60, TeclasNeutras(), False)
            if fase.jogador.estado == "aterrissando":
                break
        self.assertEqual(fase.jogador.estado, "aterrissando")
        self.assertFalse(fase.jogador.morto)

    def test_bueiro_movel_reage_ao_salto(self):
        fase = Fase(1)
        bueiro = next(item for item in fase.buracos if isinstance(item, BuracoMovel))
        fase.jogador.x = bueiro.pos_a
        fase.jogador._atualizar_rect()
        fase.jogador.pular()
        estado_inicial = bueiro.atual
        fase.atualizar(1 / 60, TeclasNeutras(), False)
        self.assertNotEqual(bueiro.atual, estado_inicial)
        self.assertFalse(fase.jogador.morto)

    def test_animacao_do_buraco_nao_estica_o_personagem_inteiro(self):
        fase = Fase(0)
        bueiro = fase.buracos[0]
        fase.jogador.iniciar_queda_buraco(bueiro.largura)
        maior_largura = max(quadro.get_width() for quadro in fase.jogador.animacoes["buraco"].quadros)
        self.assertLess(maior_largura, bueiro.largura)
        self.assertLessEqual(maior_largura, LARGURA_BUEIRO_ANIMACAO_MAX)

    def test_placa_cai_por_proximidade_sem_exigir_pulo(self):
        fase = Fase(4)
        placas = [item for item in fase.obstaculos if isinstance(item, PlacaQueCai)]
        placa = placas[-1]
        fase.jogador.x = placa.x - placa.distancia_gatilho - 12
        fase.jogador._atualizar_rect()
        fase.atualizar(1 / 60, TeclasNeutras(), False)
        self.assertEqual(placa.estado, "suspensa")

        fase.jogador.x = placa.x - placa.distancia_gatilho + 12
        fase.jogador._atualizar_rect()
        fase.atualizar(1 / 60, TeclasNeutras(), False)
        self.assertEqual(placa.estado, "caindo")
        self.assertFalse(fase.jogador.morto)

    def test_placa_tem_tempo_extra_para_pular(self):
        placa = PlacaQueCai(1000)
        tempo_queda = (CHAO_Y - placa.altura - placa.inicial_y) / placa.velocidade_queda
        self.assertGreaterEqual(placa.distancia_gatilho, 420)
        self.assertGreaterEqual(tempo_queda, 0.7)

    def test_placa_usa_apenas_area_visivel_como_hitbox(self):
        placa = PlacaQueCai(1000)
        placa.estado = "caindo"
        placa.y = CHAO_Y - placa.altura
        placa._atualizar_hitbox()

        self.assertLess(placa.hitbox.width, placa.largura_canvas / 4)
        self.assertLess(placa.hitbox.left, placa.x)
        self.assertGreater(placa.hitbox.right, placa.x)

        jogador_longe_da_arte = pygame.Rect(
            placa.x - placa.largura_canvas / 2 + 12,
            placa.hitbox.y,
            34,
            88,
        )
        self.assertFalse(placa.hitbox.colliderect(jogador_longe_da_arte))

    def test_cone_respeita_limite_antes_da_placa(self):
        fase = Fase(0)
        cone = next(item for item in fase.obstaculos if isinstance(item, ConeRolante))
        limite_final = cone.limites[1]
        for _ in range(300):
            cone.atualizar(1 / 60, fase)
        self.assertLessEqual(cone.x, limite_final)
        self.assertLess(limite_final, 2300)

    def test_cone_fica_em_trecho_delimitado_sem_invadir_bueiro(self):
        for indice in (0, 3, 4):
            fase = Fase(indice)
            cones = [item for item in fase.obstaculos if isinstance(item, ConeRolante)]
            bueiros = fase.buracos + [item for item in fase.obstaculos if isinstance(item, Buraco)]

            for cone in cones:
                for limite in cone.limites:
                    cone.x = limite
                    cone._atualizar_hitbox()
                    visual_cone = pygame.Rect(
                        round(cone.x - cone.largura / 2),
                        CHAO_Y - cone.altura,
                        cone.largura,
                        cone.altura,
                    )
                    for bueiro in bueiros:
                        estados = (0, 1) if isinstance(bueiro, BuracoMovel) else (None,)
                        for estado in estados:
                            if estado is not None:
                                bueiro.atual = estado
                                bueiro._atualizar_hitbox()
                            self.assertFalse(visual_cone.colliderect(bueiro.hitbox))

    def test_respawn_fica_visivel_e_protegido(self):
        self.assertGreaterEqual(TEMPO_RESPAWN, 1.2)
        fase = Fase(0)
        fase._registrar_morte("morte")
        for _ in range(70):
            fase.atualizar(1 / 60, TeclasNeutras(), False)
            if fase.jogador.estado == "respawn":
                break
        self.assertEqual(fase.jogador.estado, "respawn")
        self.assertFalse(fase.jogador.morto)
        tempo_restante = TEMPO_RESPAWN - fase.jogador.tempo_estado
        for _ in range(max(1, int(tempo_restante * 60) - 1)):
            fase.atualizar(1 / 60, TeclasNeutras(), False)
        self.assertEqual(fase.jogador.estado, "respawn")

    def test_respawn_nao_aceita_movimento_ate_terminar(self):
        fase = Fase(0)
        fase._reexibir_jogador()
        x_inicial = fase.jogador.x

        fase.atualizar(1 / 60, TeclasDireita(), True)
        self.assertEqual(fase.jogador.estado, "respawn")
        self.assertTrue(fase.jogador.no_chao)
        self.assertEqual(fase.jogador.vx, 0.0)
        self.assertEqual(fase.jogador.x, x_inicial)

        for _ in range(30):
            fase.atualizar(1 / 60, TeclasDireita(), False)
        self.assertEqual(fase.jogador.estado, "respawn")
        self.assertEqual(fase.jogador.x, x_inicial)

        fase.jogador.tempo_estado = TEMPO_RESPAWN
        fase.atualizar(1 / 60, TeclasDireita(), False)
        self.assertGreater(fase.jogador.x, x_inicial)

    def test_calcada_eh_repetida_em_faixa_alinhada(self):
        fase = Fase(0)
        self.assertIsNotNone(fase.calcada_tile)
        textura, passo = fase.calcada_tile
        self.assertGreater(passo, 0)
        self.assertLessEqual(textura.get_height(), 58)
        tela = pygame.Surface((1280, ALTURA))
        tela.fill((0, 0, 0))
        fase.desenhar_chao(tela)
        self.assertNotEqual(tela.get_at((10, ALTURA - 4))[:3], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
