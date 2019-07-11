class Calculadora(object):

    def __init__(self, intervaloDeConfianca):
        # intervaloDeConfianca
        self.ic = intervaloDeConfianca
        self.k = self.n = self.ex = self.ex2 = 0.0

    def adicionaValor(self, x):
        if self.n == 0:
            self.k = x
        self.n += 1
        self.ex += x - self.k
        self.ex2 += (x - self.k) * (x - self.k)

    def get_media(self):
        return self.k + (self.ex / self.n)

    def get_variancia(self):
        #if (self.n == 0 or self.n == 1):
        #    return 0
        return (self.ex2 - (self.ex*self.ex)/self.n) / (self.n-1)
