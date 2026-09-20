# Nem Tão Logo Ali - Design Specification

## Goal

Entregar uma versão jogável e demonstrável de **Nem Tão Logo Ali**, um jogo 2D de plataforma em Pygame, com cinco fases em ordem, pontuação, ranking Top 10 e integração funcional com Django para registrar jogadores e resultados.

## Requisitos de origem

O `GDD.pdf` é a fonte normativa do produto. O tutorial de Pygame é apenas material didático e não substitui o GDD.

Requisitos funcionais:

- O jogo deve ter exatamente cinco fases obrigatórias, liberadas em ordem.
- As fases são: A Rua, Em Obras, A Avenida, O Atalho e O Último Quarteirão.
- O objetivo é atravessar cada fase e chegar à porta de casa ao final da quinta fase.
- O personagem deve se mover para esquerda/direita, pular, pausar, reiniciar e reaparecer rapidamente após falha.
- Obstáculos podem ser fixos, móveis, temporizados, acionados por proximidade/salto/contato ou sequenciais, mas devem ser previsíveis após tentativa.
- Fases 2 a 5 podem possuir checkpoint; o respawn deve usar o último checkpoint ativado.
- Pontuação: concluir fase `+300`; concluir sem morte `+150`; primeiro checkpoint ativado `+50`; morte `-25`, sem permitir pontuação negativa; bônus de tempo de até `+200` por fase.
- O ranking deve exibir pelo menos as dez melhores pontuações, ordenadas por pontuação decrescente, mortes crescentes e tempo crescente.
- O resultado final deve registrar jogador, pontuação total, mortes, tempo real e data.
- O servidor Django deve armazenar jogadores e resultados e fornecer endpoints para registrar resultados e consultar ranking.
- A interface deve estar em PT-BR e manter HUD discreto com fase, pontuação, mortes e tempo.

Requisitos de qualidade:

- O programa deve iniciar sem servidor Django para permitir demonstração local, usando ranking offline como fallback; quando o servidor estiver disponível, o resultado final deve ser enviado ao Django.
- Sprites de uma mesma animação devem ter frames em ordem numérica, margens transparentes removidas para fins de escala e uma âncora consistente pelos pés/centro, evitando deslocamento visual entre frames.
- O código deve separar cenas, lógica de fase, jogador, obstáculos, pontuação/tempo, carregamento de assets e cliente Django.
- A execução deve ser documentada para Windows com Python, Pygame e Django.

## Architecture

### Cliente Pygame

`main.py` será apenas o ponto de entrada e o loop principal. Um objeto `Jogo` manterá o estado compartilhado da partida, o cliente Django e a cena atual. As cenas serão objetos com ciclo `entrar`, `atualizar` e `desenhar`:

- `MenuCena`: Jogar, Instruções, Ranking e Sair.
- `InstrucoesCena`: controles e regras essenciais.
- `IdentificacaoCena`: entrada e validação do apelido.
- `JogoCena`: controla a fase atual, pausa, reinício, progressão 1-5 e transições rápidas.
- `ResultadoCena`: mostra pontuação, mortes, tempo, status do envio e opção de voltar.
- `RankingCena`: carrega Top 10 do Django ou do arquivo offline.

`Fase` continuará sendo a unidade de simulação do mundo. Cada plano de fase declarará largura, spawn, porta, checkpoint e obstáculos. A atualização seguirá a ordem: entrada do jogador, física, obstáculos, colisões, respawn, conclusão e câmera. O desenho seguirá fundo, chão, obstáculos, personagem e HUD.

### Animação e assets

O carregador de assets terá uma função de normalização que:

1. localiza arquivos com o padrão `<nome>-<número>.png`;
2. ordena pelo sufixo inteiro, nunca pela ordem lexicográfica;
3. recorta o retângulo alfa não transparente;
4. escala preservando proporção dentro da altura-alvo;
5. compõe o frame em uma tela de tamanho estável, alinhada pelo centro horizontal e pela base;
6. retorna pelo menos um frame de fallback quando o asset estiver ausente.

As hitboxes usarão dimensões do personagem, não o retângulo transparente original do PNG. A mesma regra será usada ao trocar entre parada, corrida, pulo, queda, aterrissagem, morte e respawn.

### Django

O app `jogo` manterá:

- `Jogador(nome, criado_em)` com nome único;
- `Resultado(jogador, pontuacao, mortes, tempo, data)` com ordenação por pontuação, mortes, tempo e data.

Endpoints JSON:

- `POST /api/resultados/`: valida dados, cria/recupera o jogador, registra resultado e devolve a posição do resultado.
- `GET /api/ranking/?limite=10`: devolve no máximo 50 entradas, uma melhor pontuação por jogador, ordenadas e com posição.

O cliente deve tratar indisponibilidade, respostas inválidas e dados malformados sem travar o jogo. Ao falhar no envio, deve salvar uma cópia local ordenada em `offline_ranking.json` e exibir claramente que o modo está offline.

## Data flow

1. O jogador informa o apelido.
2. `Jogo.iniciar_partida` zera pontuação, mortes e tempo e instancia a Fase 1.
3. Ao concluir uma fase, `Fase` aplica os bônus e `JogoCena` instancia a próxima fase.
4. Após a Fase 5, `Jogo` finaliza a partida e `ResultadoCena` envia o agregado ao cliente Django.
5. O cliente tenta o Django; em caso de falha, grava o resultado localmente.
6. A cena de ranking consulta o servidor e mostra fallback local quando necessário.

## Error handling

- Nome vazio vira `Jogador` somente após validação; nomes maiores que 20 caracteres são truncados no cliente e no servidor.
- Pontuação, mortes e tempo negativos são normalizados para zero no servidor.
- JSON inválido, método HTTP incorreto e falhas de conexão retornam erros HTTP apropriados e nunca interrompem o Pygame.
- Assets ausentes não impedem a inicialização: o carregador cria uma imagem de fallback.
- A janela pode ser fechada em qualquer cena sem exceção não tratada.

## Verification strategy

- Testes unitários de ordenação numérica e normalização de animação.
- Testes de pontuação, penalidade sem pontuação negativa, checkpoint e bônus de tempo.
- Smoke test que instancia e conclui as cinco fases em modo headless.
- Teste de fluxo das cenas: menu, identificação, partida completa, resultado e ranking.
- Testes Django para criação de jogador/resultado, validação das entradas, ranking Top 10 e desempate.
- Verificação manual/visual em janela Pygame para confirmar alinhamento dos sprites, HUD e transições.

## Out of scope

- Multiplayer, autenticação de usuários, sons/música, instalação empacotada e hospedagem pública.
- Aleatoriedade não determinística nos obstáculos: os padrões devem ser repetíveis para permitir aprendizado.
