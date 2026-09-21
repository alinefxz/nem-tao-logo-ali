# Nem Tão Logo Ali

Jogo 2D de plataforma em Pygame: o personagem atravessa cinco trechos do caminho até a porta de casa. Os cenários são desenhados em camadas com câmera lateral e incluem ruas residenciais, obras, avenida com semáforo e carros, atalho com parque e o último quarteirão com a casa no lado final da tela.

## Requisitos

- Python 3.10 ou superior
- `pygame-ce`
- `Django`

Instale as dependências no Windows:

```powershell
python -m pip install pygame-ce django
```

## Executar somente o jogo

O jogo funciona sem servidor. Quando o Django estiver indisponível, os resultados são salvos em `offline_ranking.json`.

```powershell
python main.py
```

Controles: A/D ou setas para andar; Shift para correr; S ou seta para baixo para abaixar; Espaço, W ou seta para cima para pular; Esc para pausar; R para reiniciar a fase.

## Executar com o Django

Em um terminal:

```powershell
python server\manage.py migrate
python server\manage.py runserver
```

Em outro terminal:

```powershell
python main.py
```

O cliente usa `http://127.0.0.1:8000` por padrão. Para apontar para outro endereço:

```powershell
$env:NEM_TAO_LOGO_SERVER = "http://127.0.0.1:8000"
python main.py
```

Endpoints:

- `POST /api/resultados/` registra nome, pontuação, mortes e tempo.
- `GET /api/ranking/?limite=10` retorna o Top 10, com no máximo 50 entradas e uma melhor pontuação por jogador.

## Fases e pontuação

As fases são liberadas em ordem: A Rua, Em Obras, A Avenida, O Atalho e O Último Quarteirão. Cada fase concede 300 pontos, bônus de até 200 pelo tempo, 150 sem mortes e 50 no primeiro checkpoint. Cada morte desconta 25 pontos, sem deixar o total negativo.

## Verificação

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python server\manage.py test jogo -v 2
python testes_smoke.py
python testes_cenas.py
```
