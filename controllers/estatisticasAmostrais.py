class EstatisticasAmostrais(object):
    def __init__(self):
        self.soma = self.somaQuad = self.n = self.x = 0.0
    
    def adicionaValor(self, x):
            if self.n == 0:
                    self.k = x
            self.n += 1
            self.soma += x - self.k
            self.somaQuad += (x - self.k)*(x - self.k)
    def get_muChapeu(self):
            return self.k + self.soma / self.n

    def get_sigmaChapeu(self):
            return (self.somaQuad - (self.soma*self.soma)/self.n)/(self.n - 1)