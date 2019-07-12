import math
#from scipy import stats
from scipy.stats import chi2
#import matplotlib
import matplotlib.pyplot as plt
import numpy as np

class Calculadora(object):
    def __init__(self):
        self.aprovado = ""

    def ICDaMedia(self, mean_list):
        tStudent = 1.645   #T-student para mais de 120 amostras

        #qtd de amostras
        n = len(mean_list)

        #média amostral
        mean = np.sum(mean_list)/n

        #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
        s = math.sqrt(np.sum([(float(element) - float(mean))**2 for element in mean_list])/(n-1.0))

        #calculo do Intervalo de Confiança pela T-student
        lower = mean - (tStudent*(s/math.sqrt(n)))
        upper = mean + (tStudent*(s/math.sqrt(n)))

        center = lower + (upper - lower)/2.0

        if (center/10.0 < (upper - lower)):
            #print center/10.0
            #print upper - lower
            self.aprovado = False
            #print "teste IC da media não obteve precisao de 5%, intervalo maior do que 10% do valor central"
        else:
            self.aprovado = True

        #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
        return (lower, upper, center, self.aprovado)


    def ICDaVariacia(self, mean_list):
        #esse método utilizará a formula do qui-quadrado para medir a variancia

        #qtd de amostras
        n = len(mean_list)

        #média amostral
        mean = np.sum(mean_list)/n

        #dados obtidos na tabela da qui-quadrada para alpha=0.5, alpha/2 = 0.25
        #Qalpha2 = 74.222
        #Q1menosalpha2 = 129.561

        #como na tabela de qui-quadrado só temos ate 100 graus de liberdade, tivemos que usar uma funcao
        #auxiliar para calcular o valor dela para n = 3200

        Qalpha2 = chi2.isf(q=0.025, df=n-1)
        Q1menosalpha2 = chi2.isf(q=0.975, df=n-1)

        #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
        s_quadrado = np.sum([(float(element) - float(mean))**2 for element in mean_list])/(n-1.0)

        #calculo do Intervalo de Confiança pela qui-quadrado
        lower = (n-1)*s_quadrado/Q1menosalpha2
        upper = (n-1)*s_quadrado/Qalpha2

        center = lower + (upper - lower)/2.0

        if center/10.0 < (upper - lower):
            #print center/10.0
            #print upper - lower
            self.aprovado = False
            #print "teste IC da variancia não obteve precisao de 5%, intervalo maior do que 10% do valor central"
        else:
            self.aprovado = True

        #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
        return (lower, upper, center, self.aprovado)

    #c.plotGrafico(x, y, x_legenda, y_legenda)
    def plotGrafico(self, x, y, x_legenda='x', y_legenda='y', saida='plot'):
        fig, ax = plt.subplots()
        ax.plot(range(x), y)
        ax.set(xlabel=x_legenda, ylabel=y_legenda, title='Simulador M/M/1')
        ax.grid()

        fig.savefig(saida + '.png')
        #plt.show()
