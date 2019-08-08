class Calculadora2(object):
    def __init__(self):
        self.soma = self.somaQuad = self.n = self.x = self.k = 0.0
    
    def adicionaValor(self, x):
        if self.n == 0:
            self.k = x
        self.n += 1
        self.soma += x - self.k
        self.somaQuad += (x - self.k)*(x - self.k)
    
    def getMuChapeu(self):
        return self.k + self.soma / self.n

    def getSigmaChapeu(self):
        #return ((self.somaQuad - (self.soma*self.soma)/self.n)/(self.n-1))
        try: return ((self.somaQuad - (self.soma*self.soma)/self.n)/(self.n-1))
        except ZeroDivisionError: return ((self.somaQuad - (self.soma*self.soma)/self.n+1)/(self.n))
