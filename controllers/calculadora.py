import math
from scipy.stats import chi2
import scipy.stats
import matplotlib.pyplot as plt
import numpy as np

class Calculadora(object):
    def __init__(self):
        self.ok = ""
        self.precisaoIC = 0.1
    def ICMedia(self, media, variancia, n , v_analitico):
        nQuad = math.sqrt(n)
        s = math.sqrt(variancia)
        tStudent = 1.960 # T-student para n>30 amostras


        # Variância das amostras: SOMA((Media - Media das amostras)^2) = S^2
        #s = math.sqrt(np.sum([(float(element) - float(media))**2 for element in lista_de_medias])/(n-1.0))
        inf = media - (tStudent*(s/nQuad)) # IC(inferior) pela T-student
        sup = media + (tStudent*(s/nQuad)) # IC(superior) pela T-student
        centro = inf + (sup - inf)/2.0 # Centro dos intervalos

        # Se intervalo for maior do que 10% do valor central(precisão de 5%), não atingiu precisão adequada
        p_tStudent = tStudent*(s/(media*nQuad))
        if (p_tStudent <= self.precisaoIC) == True and (inf <= v_analitico)== True and (sup >= v_analitico)== True:
            self.ok = True
        else :
            self.ok = False
        
        # retorna o limite inferior, limite superior, o valor central e se atingiu a precisão
        return (inf, sup, centro, self.ok, p_tStudent)
                
    def ICVariancia(self, media, variancia, n, v_analitico):
        # Qui-quadrado para medir a variância
        #s  = math.sqrt(variancia)
        s_quadrado = media
        sobreposicaoICs = False

        # Usando função auxiliar (chi2.isf) para calcular o valor de qui-quadrado para n = 3200
        qui2Alpha = chi2.isf(q=0.025, df=n-1)
        qui2MenosAlpha = chi2.isf(q=0.975, df=n-1)
        #print(f'qui2alpha = {qui2Alpha}; qui2MenosAlpha = {qui2MenosAlpha}')
        

        # Calculo do IC para qui-quadrado
        supChi = ((n-1)*s_quadrado)/qui2MenosAlpha
        infChi = ((n-1)*s_quadrado)/qui2Alpha
        centroChi = infChi + (supChi - infChi)/2.0

        p_chi2 = (qui2Alpha - qui2MenosAlpha)/ (qui2Alpha + qui2MenosAlpha)

        # Calcula o IC da variancia pela tStudent
        nQuad = math.sqrt(n)
        s = math.sqrt(variancia)
        tStudent = 1.960 # T-student para n>30 amostras


        # Variância das amostras: SOMA((Media - Media das amostras)^2) = S^2
        #s = math.sqrt(np.sum([(float(element) - float(media))**2 for element in lista_de_medias])/(n-1.0))
        infT = media - (tStudent*(s/nQuad)) # IC(inferior) pela T-student
        supT = media + (tStudent*(s/nQuad)) # IC(superior) pela T-student
        centroT = infT + (supT - infT)/2.0 # Centro dos intervalos

        # Se intervalo for maior do que 10% do valor central(precisão de 5%), não atingiu precisão adequada
        p_tStudent = tStudent*(s/(media*nQuad))
        #print(f'precisao tStudent: {p_tStudent}')
        #print(f'IC Var T; sup: {supT}; inf: {infT}; centro: {centroT}')
        # Verificar se ha sobreposicao completa das duas ICs calculadas
        if (infT <= centroChi <= supT) ==True and (infChi <= centroT <= supChi)==True:
            sobreposicaoICs = True
        #print(f'precisao chi: {p_chi2}')
        if (p_chi2 and p_tStudent <= self.precisaoIC) == True and (infChi <= v_analitico <= supChi)== True and (infT <= v_analitico <= supT)== True and sobreposicaoICs == True:
            self.ok = True
        else :
            self.ok = False
         
        #print((p_chi2 and p_tStudent <= self.precisaoIC), (infChi <= v_analitico <= supChi), (infT <= v_analitico <= supT), sobreposicaoICs )
        # retorna o limite inferior, limite superior, o valor central e se está dentro do intervalo
        return (infChi, supChi, centroChi, self.ok, p_chi2, centroT, p_tStudent, infT, supT, sobreposicaoICs)

    '''
    def ICMedia(self, lista_de_medias):
        tStudent = 1.645 # T-student para 120 amostras
        n = len(lista_de_medias) # Quantidade de amostras
        media = np.sum(lista_de_medias)/n # Média das amostras

        # Variância das amostras: SOMA((Media - Media das amostras)^2) = S^2
        s = math.sqrt(np.sum([(float(element) - float(media))**2 for element in lista_de_medias])/(n-1.0))
        inf = media - (tStudent*(s/math.sqrt(n))) # IC(inferior) pela T-student
        sup = media + (tStudent*(s/math.sqrt(n))) # IC(superior) pela T-student
        centro = inf + (sup - inf)/2.0 # Centro dos intervalos

        # Se intervalo for maior do que 10% do valor central(precisão de 5%), não atingiu precisão adequada
        if (centro/10.0 < (sup - inf)):
            self.ok = False
        else:
            self.ok = True

        # retorna o limite inferior, limite superior, o valor central e se atingiu a precisão
        return (inf, sup, centro, self.ok)
            
    def ICVariancia(self, lista_de_medias):
        # Qui-quadrado para medir a variância
        n = len(lista_de_medias) # Quantidade de amostras
        media = np.sum(lista_de_medias)/n # Média das amostras

        # Usando função auxiliar (chi2.isf) para calcular o valor de qui-quadrado para n = 3200
        qui2Alpha = chi2.isf(q=0.025, df=n-1)
        qui2MenosAlpha = chi2.isf(q=0.975, df=n-1)

        # Variância das amostras: SOMA((Media - Media das Amostras)^2) = S^2
        s_quadrado = np.sum([(float(element) - float(media))**2 for element in lista_de_medias])/(n-1.0)

        # Calculo do IC para qui-quadrado
        inf = (n-1)*s_quadrado/qui2MenosAlpha
        sup = (n-1)*s_quadrado/qui2Alpha
        centro = inf + (sup - inf)/2.0

        if centro/10.0 < (sup - inf): # Se for maior do que 10% do valor central(precisão de 5%)
            self.ok = False #então não atingiu a precisão adequada
        else:
            self.ok = True

        # retorna o limite inferior, limite superior, o valor central e se está dentro do intervalo
        return (inf, sup, centro, self.ok)
    
    def ICVarianciaIncremental(self, lista_de_medias):
        # Qui-quadrado para medir a variância
        n = len(lista_de_medias)  # Quantidade de amostras

        # Usando função auxiliar (chi2.isf) para calcular o valor de qui-quadrado para n = 3200
        qui2Alpha = chi2.isf(q=0.025, df=n - 1)
        qui2MenosAlpha = chi2.isf(q=0.975, df=n - 1)

        # Variância das amostras: SOMA((Media - Media das Amostras)^2) = S^2
        # s_quadrado = np.sum([(float(element) - float(media)) ** 2 for element in lista_de_medias]) / (n - 1.0)

        s_quadrado_1termo = 0.0
        for element in lista_de_medias:
            s_quadrado_1termo = s_quadrado_1termo + float(element) ** 2
        s_quadrado_1termo = s_quadrado_1termo / (n - 1.0)

        s_quadrado_2termo = 0.0
        for element in lista_de_medias:
            s_quadrado_2termo = s_quadrado_2termo + float(element)
        s_quadrado_2termo = (s_quadrado_2termo ** 2) / (n * (n - 1.0))

        s_quadrado = s_quadrado_1termo - s_quadrado_2termo

        # Calculo do IC para qui-quadrado
        inf = (n - 1) * s_quadrado / qui2MenosAlpha
        sup = (n - 1) * s_quadrado / qui2Alpha
        centro = inf + (sup - inf) / 2.0

        if centro / 10.0 < (sup - inf):  # Se for maior do que 10% do valor central(precisão de 5%)
            self.ok = False  # então não atingiu a precisão adequada
        else:
            self.ok = True

        # retorna o limite inferior, limite superior, o valor central e se está dentro do intervalo
        return (inf, sup, centro, self.ok)
    '''

    def tstudent(self, alpha, gl):
        return scipy.stats.t.ppf(alpha, df=gl)

    def plotGrafico(self, x, y, disciplina, x_legenda='x', y_legenda='y', saida='plot'):
        fig, ax = plt.subplots()
        ax.plot(range(x), y)
        #ax.plot(x,y)
        ax.set(xlabel=x_legenda, ylabel=y_legenda, title=disciplina.upper())
        #ax.set_ylim(0, 1)
        ax.grid()
        fig.savefig(saida + '.png')
