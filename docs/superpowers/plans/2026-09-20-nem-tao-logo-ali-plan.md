# Nem Tão Logo Ali Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o protótipo em um jogo Pygame completo com cinco fases, progressão, pontuação, ranking e persistência Django, corrigindo também o carregamento/alinhamento dos sprites.

**Architecture:** Um loop Pygame fino delegará o estado para cenas (`MenuCena`, `InstrucoesCena`, `IdentificacaoCena`, `JogoCena`, `ResultadoCena`, `RankingCena`). `Fase` continuará encapsulando simulação, obstáculos, câmera e conclusão. O cliente Django terá fallback local e o servidor Django será responsável pelo ranking persistido.

**Tech Stack:** Python 3.10+, Pygame/Pygame-ce, Django, SQLite, `unittest`, modo SDL headless para testes.

**Spec:** `docs/superpowers/specs/2026-09-20-nem-tao-logo-ali-design.md`

## Global Constraints

- O jogo deve ter exatamente cinco fases obrigatórias liberadas em ordem.
- As fases devem ser A Rua, Em Obras, A Avenida, O Atalho e O Último Quarteirão.
- Pontuação: concluir fase `+300`, concluir sem morte `+150`, primeiro checkpoint `+50`, morte `-25` sem pontuação negativa e bônus de tempo máximo de `+200` por fase.
- O ranking deve mostrar pelo menos as dez melhores pontuações e desempatar por pontuação, mortes e tempo.
- O resultado final deve registrar jogador, pontuação total, mortes, tempo e data.
- O cliente deve funcionar sem o servidor, mas enviar o resultado final ao Django quando o servidor estiver disponível.
- Animações devem ordenar frames numericamente, recortar transparência e alinhar todos os frames por centro/base.
- A interface do jogo e as mensagens do servidor devem permanecer em PT-BR.
- Não incluir as alterações locais já existentes nos sprites em commits de código sem verificar cada arquivo individualmente.

## Review Focus

- Apelido vazio, contendo espaços ou maior que 20 caracteres deve ser validado sem travar a troca de cena; teste em `IdentificacaoCena`.
- Um frame com dimensões muito diferentes ou margem transparente grande não pode deslocar o personagem; teste no normalizador de animação.
- Morte no instante em que a pontuação é zero não pode produzir pontuação negativa; teste no gerenciador de pontuação.
- O servidor desligado durante envio ou consulta não pode encerrar o Pygame; teste no cliente Django com arquivo offline.
- O jogador não pode concluir a Fase 5 e registrar resultado antes de concluir as fases anteriores; teste no controlador de progressão.

---

### Task 1: Corrigir o núcleo do jogador, interface e carregamento de animações

**Files:**
- Modify: `scripts/assets.py`
- Modify: `scripts/animacao.py`
- Replace: `scripts/jogador.py`
- Replace: `scripts/interfaces.py`
- Create: `tests/test_assets_jogador.py`

**Interfaces:**
- Produces `carregar_animacao(pasta: str, nome: str, altura: int, n_frames: int | None = None) -> list[pygame.Surface]` com frames normalizados.
- Produces `normalizar_frame(imagem: pygame.Surface, altura: int, largura_canvas: int | None = None) -> pygame.Surface`.
- Produces `Jogador(x: float, y: float, altura: int = ALTURA_JOGADOR)` com `mover(direcao)`, `pular()`, `atualizar(dt, solidos, plataformas)`, `morrer(motivo)`, `reiniciar(x, y)`, `definir_estado(nome)`, `desenhar(tela, camera_x, alpha=255)` e `rect`.
- Produces `Texto` e `Botao`; `Botao.get_click(eventos)` deve depender de `MOUSEBUTTONDOWN`, não do estado global do mouse.

- [ ] **Step 1: Write the failing tests**

```python
class TestAssetsJogador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_frames_are_sorted_by_numeric_suffix_and_share_canvas(self):
        frames = carregar_animacao("personagem", "parada", 88)
        self.assertGreaterEqual(len(frames), 2)
        self.assertEqual(len({frame.get_size() for frame in frames}), 1)

    def test_player_constructor_matches_phase_api(self):
        jogador = Jogador(100, 600)
        self.assertEqual(jogador.rect.bottom, 600)
        self.assertGreater(jogador.rect.width, 0)

    def test_button_uses_click_event(self):
        surface = pygame.Surface((100, 60))
        button = Botao(surface, "Jogar", 10, 10, 24, (20, 20, 20), (255, 255, 255))
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(20, 20), button=1)
        self.assertTrue(button.get_click([event]))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

Expected: FAIL because `tests/` and the requested constructor/normalization APIs do not yet exist and the current interface contains invalid citation text.

- [ ] **Step 3: Implement the minimal core**

Implement numeric frame discovery, alpha cropping, proportional scaling and bottom-center composition in `scripts/assets.py`. Rewrite `scripts/jogador.py` around a world-coordinate rectangle, gravity, horizontal movement, jump state, animation state and the fixed constructor above. Rewrite `scripts/interfaces.py` without citation artifacts, with `Texto.atualizarTexto`, `Texto.desenhar`, `Botao.desenhar` and event-based `Botao.get_click`.

- [ ] **Step 4: Run the focused tests**

Run: `python -m unittest tests.test_assets_jogador -v`

Expected: PASS for frame normalization, constructor compatibility and event-based button clicks.

- [ ] **Step 5: Run the full current suite and commit**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

Expected: PASS for all tests created so far.

```powershell
git add scripts/assets.py scripts/animacao.py scripts/jogador.py scripts/interfaces.py tests/test_assets_jogador.py
git commit -m "fix: normalize assets and repair player core"
```

### Task 2: Consolidar pontuação, tempo e cinco fases

**Files:**
- Modify: `scripts/config.py`
- Modify: `scripts/pontuacao.py`
- Modify: `scripts/tempo.py`
- Modify: `scripts/fase.py`
- Modify: `scripts/fases_planos.py`
- Modify: `scripts/obstaculos.py`
- Create: `tests/test_regras_fases.py`
- Replace: `testes_smoke.py`

**Interfaces:**
- `GerenciadorPontuacao` exposes `pontos`, `total_mortes`, `mortes_fase`, `nova_fase()`, `registrar_morte()`, `checkpoint(ja_contado: bool)` and `concluir_fase(bonus_tempo: int) -> int`.
- `GerenciadorTempo` exposes `iniciar_fase(indice)`, `acumular(dt)`, `tempo_fase()`, `tempo_total()`, `concluir_fase()` and `bonus_fase(indice)`.
- `Fase(indice, pontuacao=None, tempo=None)` exposes `atualizar(dt, teclas, pulou)`, `concluir_fase()`, `desenhar(tela)`, `plano`, `porta`, `jogador`, `concluida` and `resultado`.
- `contruir_plano(indice)` accepts only indices `0..4` and raises `ValueError` otherwise.

- [ ] **Step 1: Write the failing rule tests**

```python
class TestRegrasFases(unittest.TestCase):
    def test_death_penalty_never_makes_score_negative(self):
        score = GerenciadorPontuacao()
        score.registrar_morte()
        self.assertEqual(score.pontos, 0)

    def test_each_phase_has_expected_name_and_order(self):
        self.assertEqual(
            [contruir_plano(i)["nome"] for i in range(5)],
            ["A Rua", "Em Obras", "A Avenida", "O Atalho", "O Último Quarteirão"],
        )

    def test_checkpoint_bonus_is_awarded_once(self):
        score = GerenciadorPontuacao()
        self.assertTrue(score.checkpoint(False))
        self.assertEqual(score.pontos, 50)
        self.assertFalse(score.checkpoint(True))
        self.assertEqual(score.pontos, 50)
```

- [ ] **Step 2: Run the rule tests to verify failure**

Run: `python -m unittest tests.test_regras_fases -v`

Expected: FAIL because the phase plans do not expose the required names consistently and the current phase/player interfaces are inconsistent.

- [ ] **Step 3: Implement the minimal phase contract**

Add `nome` to each plan, validate indices, make `Fase` construct `Jogador` with world coordinates, ensure `nova_fase()` runs once per phase, keep checkpoints marked after respawn, and ensure `Porta` completes only the current phase. Keep the existing obstacle variety but correct any hitbox/draw call mismatch exposed by the tests.

- [ ] **Step 4: Add the five-phase headless smoke test**

The smoke test must initialize Pygame with dummy video/audio drivers, instantiate `Fase(0)` through `Fase(4)`, place the player immediately before each door, update until `concluida`, and assert that all five phases can complete and the score is non-negative.

- [ ] **Step 5: Run focused and smoke tests**

Run: `python -m unittest tests.test_regras_fases -v`

Expected: PASS for scoring, names, checkpoint behavior and phase validation.

Run: `python testes_smoke.py`

Expected: print five `CONCLUÍDA` lines and `SMOKE: OK`.

- [ ] **Step 6: Commit**

```powershell
git add scripts/config.py scripts/pontuacao.py scripts/tempo.py scripts/fase.py scripts/fases_planos.py scripts/obstaculos.py tests/test_regras_fases.py testes_smoke.py
git commit -m "feat: implement five phase rules and progression data"
```

### Task 3: Implement the complete Pygame scene flow

**Files:**
- Replace: `scripts/cenas.py`
- Replace: `main.py`
- Modify: `scripts/cliente_django.py`
- Create: `tests/test_cenas_fluxo.py`

**Interfaces:**
- `Jogo` exposes `iniciar_partida(nome)`, `finalizar_partida(pontuacao, tempo)`, `reiniciar_partida()` and state fields `nome_jogador`, `pontuacao`, `tempo`, `resultado_final` and `jogo_cena`.
- Each scene implements `entrar()`, `atualizar(dt, teclas, eventos) -> str | None` and `desenhar(tela)`.
- `JogoCena` exposes `iniciar(nome)`, `fase`, `fase_atual`, `transicao`, `atualizar(dt, teclas, eventos)` and must only advance from phase `n` to `n + 1` after `fase.concluida`.

- [ ] **Step 1: Write the failing scene tests**

```python
class TestCenasFluxo(unittest.TestCase):
    def test_identification_trims_and_limits_player_name(self):
        game = StubGame()
        scene = IdentificacaoCena(game)
        scene.entrar()
        for char in "   A" + "x" * 30:
            scene.processar_evento(pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_x, unicode=char
            ))
        self.assertEqual(scene.nome, "Axxxxxxxxxxxxxxxxxxx")

    def test_game_does_not_skip_unfinished_phases(self):
        game = StubGame()
        scene = JogoCena(game)
        scene.iniciar("Ali")
        scene.fase.concluida = False
        scene.atualizar(1 / 60, NeutralKeys(), [])
        self.assertEqual(scene.fase_atual, 0)

    def test_complete_flow_reaches_result_after_phase_five(self):
        game = StubGame()
        scene = JogoCena(game)
        scene.iniciar("Ali")
        for _ in range(5):
            scene.fase.jogador.x = scene.fase.porta.x - 20
            scene.fase.jogador.y = scene.fase.jogador.chao_y
            while not scene.fase.concluida:
                scene.atualizar(1 / 30, NeutralKeys(), [])
        self.assertGreaterEqual(game.resultado_final["pontos"], 0)
```

The test module defines `StubGame` with `resultado_final`, `iniciar_partida` and `finalizar_partida`, plus `NeutralKeys.__getitem__` returning `False` for every key.

- [ ] **Step 2: Run the scene tests to verify failure**

Run: `python -m unittest tests.test_cenas_fluxo -v`

Expected: FAIL because the current `cenas.py` contains only the old menu/Fase 1 flow and does not define the approved scene classes.

- [ ] **Step 3: Implement the scene state machine**

Create reusable scene base behavior, render PT-BR labels, make identification keyboard-driven, add pause with `Esc`, restart with `R`, return to menu, and use one shared `GerenciadorPontuacao`/`GerenciadorTempo` across all five phases. `ResultadoCena` must call `ClienteDjango.enviar_resultado` once after the fifth phase, not after phase one. `RankingCena` must refresh when entering rather than only at construction.

- [ ] **Step 4: Replace the loop entry point**

Make `main.py` initialize SDL, create `Jogo`, route events to the active scene, call `atualizar` with `dt`, draw the active scene and quit cleanly on `QUIT`. Do not leave a second legacy scene registry or hard-coded player name.

- [ ] **Step 5: Run scene tests and the existing smoke test**

Run: `python -m unittest tests.test_cenas_fluxo -v`

Expected: PASS for input validation, ordered progression and final result flow.

Run: `python testes_cenas.py`

Expected: print `CENAS: OK` with no traceback.

- [ ] **Step 6: Commit**

```powershell
git add main.py scripts/cenas.py scripts/cliente_django.py tests/test_cenas_fluxo.py testes_cenas.py
git commit -m "feat: connect menu, gameplay, result and ranking scenes"
```

### Task 4: Harden Django persistence and client fallback

**Files:**
- Modify: `server/jogo/models.py`
- Modify: `server/jogo/views.py`
- Modify: `server/jogo/urls.py`
- Modify: `server/jogo/tests.py`
- Modify: `scripts/cliente_django.py`
- Create: `tests/test_cliente_django.py`
- Modify: `README.md`

**Interfaces:**
- `POST /api/resultados/` returns `{ok: true, id: int, posicao: int}` for valid JSON.
- `GET /api/ranking/?limite=N` returns `{ranking: list}` with at most `N` unique players and fields `posicao`, `nome`, `pontuacao`, `mortes`, `tempo`, `data`.
- `ClienteDjango.enviar_resultado(nome, pontuacao, mortes, tempo)` returns `{ok, servidor, posicao}`.
- `ClienteDjango.obter_ranking(limite=10)` returns a sorted list regardless of server availability.

- [ ] **Step 1: Write Django and fallback tests**

```python
class ResultadoApiTests(TestCase):
    def test_post_resultado_creates_player_and_clamps_negative_values(self):
        response = self.client.post("/api/resultados/", data=json.dumps({
            "nome": "  Ali  ", "pontuacao": -5, "mortes": -2, "tempo": -1
        }), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        resultado = Resultado.objects.get()
        self.assertEqual(resultado.jogador.nome, "Ali")
        self.assertEqual(resultado.pontuacao, 0)
        self.assertEqual(resultado.mortes, 0)
        self.assertEqual(resultado.tempo, 0)

    def test_ranking_is_unique_per_player_and_respects_limit(self):
        for index in range(12):
            jogador = Jogador.objects.create(nome=f"J{index:02d}")
            Resultado.objects.create(jogador=jogador, pontuacao=1000 - index)
        response = self.client.get("/api/ranking/?limite=10")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ranking"]), 10)
```

- [ ] **Step 2: Run Django tests to verify failure**

Run: `python server\manage.py test jogo -v 2`

Expected: FAIL for the missing validation/unique ranking coverage or fail to import the currently incomplete test setup.

- [ ] **Step 3: Implement server validation and stable ranking**

Use a small validation helper in `views.py`, reject non-object JSON with status 400, convert numeric fields safely, clamp negatives, cap `limite` at 50, and compute one best result per player before assigning positions. Add model metadata/field help where useful without changing the required schema.

- [ ] **Step 4: Test client fallback without network**

Use a temporary ranking path and a client whose request method raises `URLError`. Assert that `enviar_resultado` returns `servidor=False`, writes valid JSON, and that `obter_ranking` returns entries sorted by score, deaths and time.

- [ ] **Step 5: Run server and client tests**

Run: `python server\manage.py test jogo -v 2`

Expected: PASS with model, endpoint and ranking assertions.

Run: `python -m unittest tests.test_cliente_django -v`

Expected: PASS with offline fallback assertions.

- [ ] **Step 6: Write and verify Windows run instructions**

Document:

```powershell
python -m pip install pygame-ce django
python server\manage.py migrate
python server\manage.py runserver
python main.py
```

Also document the offline mode, controls, five phases and API URLs.

- [ ] **Step 7: Commit**

```powershell
git add server/jogo server/casa scripts/cliente_django.py tests/test_cliente_django.py README.md
git commit -m "feat: persist results and expose top ten ranking"
```

### Task 5: Full verification and visual cleanup

**Files:**
- Modify: `scripts/assets.py` only when visual verification finds a concrete frame issue.
- Modify: `README.md` with final troubleshooting notes.
- Create: `tests/test_requisitos.py`

**Interfaces:**
- `tests/test_requisitos.py` verifies the delivered requirements without relying on a running graphical window.

- [ ] **Step 1: Write the requirement checklist tests**

```python
class TestRequisitos(unittest.TestCase):
    def test_exactly_five_phase_plans_exist(self):
        self.assertEqual(len(NOMES_FASES), 5)
        for index in range(5):
            self.assertEqual(contruir_plano(index)["nome"], NOMES_FASES[index])

    def test_score_constants_match_gdd(self):
        self.assertEqual(
            (BONUS_FASE, BONUS_SEM_MORTES, BONUS_CHECKPOINT,
             PENALIDADE_MORTE, BONUS_TEMPO_MAX),
            (300, 150, 50, 25, 200),
        )

    def test_ranking_limit_is_at_least_top_ten(self):
        client = ClienteDjango()
        self.assertLessEqual(len(client.obter_ranking(10)), 10)
```

- [ ] **Step 2: Run the tests to verify any missing requirement**

Run: `python -m unittest tests.test_requisitos -v`

Expected: FAIL only for requirements not yet wired by Tasks 1-4; fix the smallest production boundary that owns each failure.

- [ ] **Step 3: Run complete verification**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

Expected: all unit, scene, fallback and requirement tests pass.

Run: `python server\manage.py test -v 2`

Expected: all Django tests pass.

Run: `python testes_smoke.py`

Expected: five completed phases and `SMOKE: OK`.

Run: `python testes_cenas.py`

Expected: `CENAS: OK`.

- [ ] **Step 4: Perform visual check**

Start the game with `python main.py`, inspect idle/run/jump/fall/death/respawn transitions, play through one obstacle in each phase, verify HUD readability, confirm pause/restart, and open Ranking with and without the Django server. If a frame still jumps, capture the exact animation name and adjust only the normalization anchor, then rerun the full suite.

- [ ] **Step 5: Commit final verification changes**

```powershell
git add tests/test_requisitos.py README.md scripts/assets.py
git commit -m "test: verify game requirements and visual asset flow"
```
