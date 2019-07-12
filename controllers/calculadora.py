import math
#from scipy import stats
from scipy.stats import chi2
#import matplotlib
import matplotlib.pyplot as plt
import numpy as np

class Calculadora(object):
    def __init__(self):
        self.aprovado = ""

    def ICDaMedia(self, lista_de_medias):
        # T-student para 120 amostras
        tStudent = 1.645
        # Quantidade de amostras
        n = len(lista_de_medias)
        # Média das amostras
        media = np.sum(lista_de_medias)/n

        # Variância amostral:
        # usando a forma:
        # Soma((Media - Media das amostras)^2) = S^2
        s = math.sqrt(np.sum([(float(element) - float(media))**2 for element in lista_de_medias])/(n-1.0))

        # IC pela T-student
        inf = media - (tStudent*(s/math.sqrt(n)))
        sup = media + (tStudent*(s/math.sqrt(n)))
        # Centro dos intervalos
        centro = inf + (inf - sup)/2.0

        # Aqui nós verificamos se obtivemos uma precisão de 5%
        # Se intervalo for maior do que 10% do valor central, não atingiu precisão adequada
        if (centro/10.0 < (inf - sup)):
            self.ok = False
        else:
            self.ok = True

        #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
        return (inf, sup, centro, self.ok)


    def ICVariancia(self, lista_de_medias):
        # Qui-quadrado para medir a variancia
        # Quantidade de amostras
        n = len(lista_de_medias)

        # Média das amostras
        media = np.sum(lista_de_medias)/n

        # Usando função auxiliar (chi2.isf) para calcular o valor para n = 3200
        Qui_alpha2 = chi2.isf(q=0.025, df=n-1)
        Qui1_menosalpha2 = chi2.isf(q=0.975, df=n-1)

        # Variância das amostras:
        # SOMA((Media - Media das Amostras)^2) = S^2
        s_quadrado = np.sum([(float(element) - float(media))**2 for element in lista_de_medias])/(n-1.0)

        # Calculo do Intervalo de Confiança para qui-quadrado
        inf = (n-1)*s_quadrado/Qui1_menosalpha2
        sup = (n-1)*s_quadrado/Qui_alpha2
        centro = inf + (sup - inf)/2.0

        # Aqui nós verificamos se obtivemos uma precisão de 5%
        # Se intervalo for maior do que 10% do valor central, não atingiu precisão adequada
        if centro/10.0 < (sup - inf):
            self.ok = False
        else:
            self.ok = True

        #retorna o limite inferior, limite superior, o valor central e se está dentro do intervalo
        return (inf, sup, centro, self.ok)

    #c.plotGrafico(x, y, x_legenda, y_legenda)
    def plotGrafico(self, x, y, x_legenda='x', y_legenda='y', saida='plot'):
        fig, ax = plt.subplots()
        ax.plot(range(x), y)
        ax.set(xlabel=x_legenda, ylabel=y_legenda, title='Simulador M/M/1')
        ax.grid()

        fig.savefig(saida + '.png')
        #plt.show()
