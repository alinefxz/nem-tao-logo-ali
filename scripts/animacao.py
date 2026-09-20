class Animacao:
    def __init__(self, quadros, fps=10, loop=True):
        self.quadros = list(quadros) or [None]
        self.fps = max(0.1, float(fps))
        self.loop = loop
        self.tempo = 0.0
        self.indice = 0

    def atualizar(self, dt):
        self.tempo += max(0.0, dt)
        indice = int(self.tempo * self.fps)
        self.indice = indice % len(self.quadros) if self.loop else min(len(self.quadros) - 1, indice)

    def reiniciar(self):
        self.tempo = 0.0
        self.indice = 0

    def concluida(self):
        return not self.loop and self.tempo >= len(self.quadros) / self.fps

    def imagem(self):
        return self.quadros[self.indice]
