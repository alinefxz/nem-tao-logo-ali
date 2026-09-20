import pygame


class Texto:
    def __init__(self, tela, texto, x, y, cor=(255, 255, 255), tamanho=28, centralizado=False):
        pygame.font.init()
        self.tela = tela
        self.fonte = pygame.font.Font(None, tamanho)
        self.posicao = (x, y)
        self.cor = cor
        self.centralizado = centralizado
        self.texto = ""
        self.imagemTexto = None
        self.atualizarTexto(texto)

    def atualizarTexto(self, novoTexto):
        self.texto = str(novoTexto)
        self.imagemTexto = self.fonte.render(self.texto, True, self.cor)

    def desenhar(self, tela=None):
        alvo = tela or self.tela
        rect = self.imagemTexto.get_rect()
        if self.centralizado:
            rect.midtop = self.posicao
        else:
            rect.topleft = self.posicao
        alvo.blit(self.imagemTexto, rect)
        return rect


class Botao:
    def __init__(self, tela, texto, x, y, tamanho, corFundo, corTexto, largura=None, altura=None):
        self.tela = tela
        self.posicao = (x, y)
        self.corFundo = corFundo
        self.corTexto = corTexto
        self.texto = Texto(tela, texto, x, y, corTexto, tamanho)
        tamanho_texto = self.texto.imagemTexto.get_size()
        self.rect = pygame.Rect(x, y, largura or tamanho_texto[0] + 30, altura or tamanho_texto[1] + 16)
        self.texto.posicao = self.rect.center
        self.texto.centralizado = True

    def desenhar(self, tela=None):
        alvo = tela or self.tela
        mouse = pygame.mouse.get_pos()
        cor = tuple(min(255, c + 20) for c in self.corFundo) if self.rect.collidepoint(mouse) else self.corFundo
        pygame.draw.rect(alvo, cor, self.rect, border_radius=8)
        pygame.draw.rect(alvo, (255, 255, 255), self.rect, 2, border_radius=8)
        self.texto.desenhar(alvo)

    def get_click(self, eventos=None):
        for evento in eventos or []:
            if evento.type == pygame.MOUSEBUTTONDOWN and getattr(evento, "button", None) == 1:
                if self.rect.collidepoint(evento.pos):
                    return True
        return False
