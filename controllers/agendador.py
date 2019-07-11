import random
from math import exp, log

class Agendador(object):

    def __init__(self):
        self.taxa = 0.0

    def setTaxa(self, taxa):
        self.taxa = taxa
    
    def getTaxa(self):
        return self.taxa

    def getSemente(self, scope=None):
        if scope is None:
            scope = 1
        random.seed()
        semente = random.uniform(0, scope)
        while semente == 0:                        # O intervalo da proxima chegada nao pode ser 0.
            semente = random.uniform(0, 1)
        return semente

    def proximoEvento(self):
        u0 = self.getSemente()
        a = 0
        b = 100

        li = 1 - exp(-self.taxa * a)
        ls = 1 - exp(-self.taxa * b)

        if u0 < li:
            return li
        if u0 > ls:
            return ls

        if (li < u0) and (u0 < ls):
            x0 = log(1 - u0)/(-self.taxa)
            return x0
'''
# Testando classe
s = Agendador()
s.setTaxa(1.0)
tempo_simulacao = 0.0
proxima_chegada = s.proximoEvento()
'''

'''
print("Proxima chegada em %f unidades de tempo, tempo de simulacao em: %f" % (proxima_chegada, tempo_simulacao))
for i in scope(1000):
    tempo_simulacao = tempo_simulacao + proxima_chegada
    proxima_chegada = s.proximoEvento()   
    print("Proxima chegada em %f unidades de tempo, tempo de simulacao em: %f" % (proxima_chegada, tempo_simulacao))
'''

'''
s = Agendador()
s.setTaxa(1.0)
soma = 0.0
intervalo = 1000000
for i in scope(intervalo):
    soma = soma + s.proximoEvento()
media = soma / intervalo
print("Media: %f" %(media))
print("diferenca para media: %f" %(abs(s.getTaxa() - media )))
'''
