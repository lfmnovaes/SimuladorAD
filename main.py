#!/usr/bin/env python3

import argparse
import datetime
from scipy import stats
import math
import random
from scipy.stats import chi2
import numpy as np
import matplotlib.pyplot as plt

from controllers.agendador import *
from controllers.calculadora import *
from models.servidor import *
from models.evento import *
from models.cliente import *

#self, tx_chegada: float, tx_servico: float, k: int, n: int, disciplina: int, IC: float, precisao: float, utilizacao: float):
#filaFCFS = Fila(0.2, 1, 100, 3200, 0, 0.95, 0.05, 0.2)

disciplina = 'fcfs'

parser = argparse.ArgumentParser(description='Simulação FCFS/LCFS')
parser.add_argument('disciplina', help='disciplina de atendimento (padrão FCFS)')
args = parser.parse_args()

if (args.disciplina.lower() == "lcfs"):
    disciplina = 'lcfs'
else:
    disciplina = 'fcfs'

class Simulador(object):
    def __init__(self, lamb, mu, k, n_rodadas, disciplina):
        self.transiente = True
        self.tx_chegada = lamb
        self.tx_servico = mu
        self.min_k = k
        self.n_rodadas = n_rodadas
        
        #FCFS ou LCFS
        self.disciplina = disciplina

        self.tempo = 0.0
        self.servidor_ocupado = False
        self.rodada_atual = -1      #-1 para fase transiente

        #listas do Simulador
        #lista de eventos que vai comandar a ordem em que acontecem as chegadas e saidas
        self.lista_de_eventos = []

        #fila da MM1, que terao clientes esperando para serem atendidos
        self.fila_de_clientes = []

        #lista para salvar dados dos clientes para a geracao de graficos
        self.todos_clientes_atendidos = []
        self.qtd_total_pessoas_fila = []

        #listas que irao guardar metricas
        self.W_barra_por_rodada = []

        #variaveis necessarias para o calculo de nq
        self.Nq_barra_por_rodada = []
        self.clientes_na_fila_evento_anterior = 0
        self.tempo_evento_anterior = 0.0
        self.tempo_inicio_rodada = 0.0
        #variável que irá guardar a área a cada chegada à fila e a cada entrada em serviço
        #nos eventos de interesse
        self.area_clientes_tempo = 0

        #lista de clientes completos por rodada, que tambem sera usado para gerar as medias por rodada
        self.clientes_atendidos_rodada = []

    def simulaTempoExponencial(self, taxa):
        r = random.random()
        # podemos utilizar dessa forma optimizada, pois tanto 1-r, quanto r sao numeros aleatorios de 0 a 1, dessa forma,
        # economizamos 1 operacao de subtracao por numero gerado
        tempo = (-1.0 * math.log(r)) / (taxa + 0.0)
        return tempo

    #funcao auxiliar para o calculo de pessoas na fila
    def somaArea(self):
        self.area_clientes_tempo += (self.tempo - self.tempo_evento_anterior ) * self.clientes_na_fila_evento_anterior

    #funcao para calcular a quantidade media de pessoas na fila da mm1
    def calculaNq(self):
        tempo_da_rodada = self.tempo - self.tempo_inicio_rodada
        self.Nq_barra_por_rodada.append(self.area_clientes_tempo/tempo_da_rodada)

    def inserirEventoEmOrdem(self, evento):
        self.lista_de_eventos.append(evento)
        #essa incersao pode ser optimizada usando busca binaria
        self.lista_de_eventos = sorted(self.lista_de_eventos, key=lambda evento: evento.tempo_evento)

    def geraEventoChegada(self, cliente):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_chegada)
        return Evento("evento_chegada", cliente, tempo_evento, self.rodada_atual)

    def geraEventoSaida(self, cliente):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_servico)
        return Evento("evento_saida", cliente, tempo_evento, self.rodada_atual)


    def testeFaseTransiente(self):
        #percentil da T-student para mais de 120 amostras
        percentil = 1.645
        #qtd de amostras
        n = len(self.clientes_atendidos_rodada)
        #média amostral
        tempos_de_fila = [cliente.tempoEmEspera() for cliente in self.clientes_atendidos_rodada]
        mean = np.sum(tempos_de_fila)/n
        #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
        s = math.sqrt(np.sum( [(float(element) - float(mean))**2 for element in tempos_de_fila] ) / (n-1.0))
        #calculo do Intervalo de Confiança pela T-student
        lower = mean - (percentil*(s/math.sqrt(n)))
        upper = mean + (percentil*(s/math.sqrt(n)))
        center = lower + (upper - lower)/2
        if center/10 < (upper - lower):
            self.transiente = False

    def adicionaWBarraDaRodada(self):
        n = float(len(self.clientes_atendidos_rodada))
        tempos_de_fila = [cliente.tempoEmEspera() for cliente in self.clientes_atendidos_rodada]
        self.W_barra_por_rodada.append( np.sum(tempos_de_fila) / n )


    def iniciaProcesso(self):
        #cria o primeiro evento de chegada para dar inicio ao simulador
        self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual)))

        while self.rodada_atual < self.n_rodadas:
            #print self.lista_de_eventos
            #funcao pop(0) retira o primeiro elemento da lista, que e o proximo evento que ira acontecer em ordem cronologica
            evento_atual = self.lista_de_eventos.pop(0)

            #print evento_atual.tipo_de_evento

            #verifica quantidade de pessoas que exitiam na fila antes de tratar o proximo evento
            self.clientes_na_fila_evento_anterior = len(self.fila_de_clientes)

            #testa para ver o tipo de evento que esta sendo tratado
            if evento_atual.tipo_de_evento == "evento_chegada":
                #atualiza o tempo global para o tempo em que o evento esta acontecendo
                self.tempo = evento_atual.tempo_evento

                #a classe cliente recebe seu tempo de chegada de acordo com o tempo do Evento que ocasionou a criacao desse cliente
                evento_atual.cliente.tempo_chegada = self.tempo

                #adiciona o cliente a fila da MM1
                self.fila_de_clientes.append(evento_atual.cliente)

                #cria uma nova chegada de cliente na lista de eventos
                self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual)))

            #se o evento nao e de entrada, entao ele e de saida
            elif evento_atual.tipo_de_evento == "evento_saida":
                #atualiza o tempo global para o tempo em que o evento esta acontecendo
                self.tempo = evento_atual.tempo_evento

                #a classe cliente recebe seu tempo de saida de acordo com o tempo do Evento que ocasionou a saida desse cliente
                evento_atual.cliente.tempo_termino_servico = self.tempo

                # servidor deixa de estar ocupado
                self.servidor_ocupado = False

                # adicionando a lista de todos os clientes atendidos para metricas globais
                self.todos_clientes_atendidos.append(evento_atual.cliente)

                # adicionando a lista de clientes atendidos nesta rodada para metricas locais
                self.clientes_atendidos_rodada.append(evento_atual.cliente)

            #depois que um dos 2 eventos ocorreu, eu irei calcular a area de clientes que esses eventos provocaram

            #faz calculo da area de pessoas por tempo para ser utilizado para calcular Nq_barra_por_rodada
            self.somaArea()

            #atualiza o valor do tempo do evento que acabou de acontecer, o proximo evento anterior
            self.tempo_evento_anterior = self.tempo

            #coleta de dados para gerar grafico
            self.qtd_total_pessoas_fila.append(len(self.fila_de_clientes))

            #Se apois os eventos ocorrerem, existir alguem na fila e o servidor estiver acabado de ser liberado
            #Entao o programa vai servir o proximo cliente que esta em espera, com relacao a politica de atendimento
            if len(self.fila_de_clientes) != 0 and not self.servidor_ocupado:
                #Se FCFS, eu irei tirar da fila de clientes o cliente que entrou a mais tempo, o cliente da esquerda
                if (self.disciplina == "fcfs"):
                    cliente = self.fila_de_clientes.pop(0)
                #Se LCFS, eu irei tirar da fila de clientes o cliente que entrou a menos tempo, o cliente da direita
                elif (self.disciplina == "lcfs"):
                    cliente = self.fila_de_clientes.pop()

                #atualiza o tempo em que o cliente entrou em servico
                cliente.tempo_comeco_servico = self.tempo

                #gera o evento de saida que essa entrada em servico ira ocasionar
                self.inserirEventoEmOrdem(self.geraEventoSaida(cliente))

                #servidor passa a estar ocupado
                self.servidor_ocupado = True

            if len(self.clientes_atendidos_rodada) >= self.min_k:
                if self.transiente:
                    #print "teste transiente"
                    self.testeFaseTransiente()
                    #print "fase transiente"
                    #print self.transiente
                    #caso chegue ao fim da fase transiente, entao comecamos a rodada 0
                    #estarei estabelecendo um fim forcado para a fase transiente caso os tempos nao consigam convergir!
                    #esse tempo será o equivalente a 10 vezes o tamanho da rodada
                    if not self.transiente or len(self.clientes_atendidos_rodada) > (10*self.min_k):
                        self.rodada_atual +=1
                        self.clientes_atendidos_rodada = []
                        self.tempo_inicio_rodada = self.tempo
                        self.area_clientes_tempo = 0
                else:
                    #gera metricas e estatisticas
                    self.calculaNq()
                    #print "clientes atendidos na rodada: "+str(len(self.clientes_atendidos_rodada))
                    self.adicionaWBarraDaRodada()

                    # limpando os clientes atendidos nesta rodada
                    self.clientes_atendidos_rodada = []
                    self.area_clientes_tempo = 0
                    self.tempo_inicio_rodada = self.tempo

                    # proxima rodada
                    #print "rodada: " + str(self.rodada_atual)
                    self.rodada_atual += 1

############# CALCULADORA ###############
def ICDaMedia(mean_list):
    #percentil da T-student para mais de 120 amostras
    percentil = 1.645

    aprovado=""

    #qtd de amostras
    n = len(mean_list)

    #média amostral
    mean = np.sum(mean_list)/n

    #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
    s = math.sqrt(np.sum( [(float(element) - float(mean))**2 for element in mean_list] ) / (n-1.0))

    #calculo do Intervalo de Confiança pela T-student
    lower = mean - (percentil*(s/math.sqrt(n)))
    upper = mean + (percentil*(s/math.sqrt(n)))

    center = lower + (upper - lower)/2.0

    if center/10.0 < (upper - lower):
        #print center/10.0
        #print upper - lower
        aprovado = False
        #print "teste IC da media não obteve precisao de 5%, intervalo maior do que 10% do valor central"
    else:
        aprovado=True

    #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
    return (lower, upper, center, aprovado)


def ICDaVariacia(mean_list):
    #esse método utilizará a formula do qui-quadrado para medir a variancia

    #qtd de amostras
    n = len(mean_list)

    aprovado=""

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
    s_quadrado=np.sum( [(float(element) - float(mean))**2 for element in mean_list] ) / (n-1.0)

    #calculo do Intervalo de Confiança pela qui-quadrado
    lower = (n-1)*s_quadrado/Q1menosalpha2
    upper = (n-1)*s_quadrado/Qalpha2

    center = lower + (upper - lower)/2.0

    if center/10.0 < (upper - lower):
        #print center/10.0
        #print upper - lower
        aprovado=False
        #print "teste IC da variancia não obteve precisao de 5%, intervalo maior do que 10% do valor central"
    else:
        aprovado=True

    #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
    return (lower, upper, center, aprovado)



#a matriz de entrada desta funcao deve ter em cada linha tuplas com a (quantidade de pessoas) ou (tempo medio no sistema) pelo periodo de cada evento
#e cada linha deve ser representativa da execucao de todo o sistema do ro respectivamente 0.2, 0.4, 0.6, 0.8 e 0.9
def printa_grafico_numero_medio_por_tempo(matriz_de_metricas_por_ro):

    for ro_metrics in matriz_de_metricas_por_ro:
        plt.plot(*zip(*ro_metrics))

    plt.legend(['ro = 0.2', 'ro = 0.4', 'ro = 0.6', 'ro = 0.8', 'ro = 0.9'], loc='upper left')

plt.show()

############# CALCULADORA ###############

if __name__ == '__main__':
    #valores_rho = [0.2, 0.4, 0.6, 0.8, 0.9]
    valores_rho = [0.9]
    mu = 1
    kmins = [150]
    n_rodadas = 3200

    #s = Simulacao()
    if (disciplina == "lcfs"):
        #s.executarLCFS()
        print(f'Executando com disciplina LCFS')
    else:
        #s.executarFCFS()
        print(f'Executando com disciplina FCFS')
        for lamb in valores_rho:
            for k in kmins:
            #for lamb in vetor_lamb:
                #self, tx_chegada: float, tx_servico: float, k: int, n: int, disciplina: int, IC: float, precisao: float, utilizacao: float):
                s = Simulador(lamb, mu, k, n_rodadas, disciplina)
                s.iniciaProcesso()

                #testando qualquer variavel para ver a corretude do simulador
                nqbarra = s.Nq_barra_por_rodada
                wbarra = s.W_barra_por_rodada

                tempos = [t.tempoEmEspera() for t in s.todos_clientes_atendidos]
                pessoas_na_fila = s.qtd_total_pessoas_fila

                lowerMW, upperMW, centerMW, aprovadoMW = ICDaMedia(wbarra)
                lowerMNq, upperMNq, centerMNq, aprovadoMNq = ICDaMedia(nqbarra)
                lowerVW, upperVW, centerVW, aprovadoVW = ICDaVariacia(wbarra)
                lowerVNq, upperVNq, centerVNq, aprovadoVNq = ICDaVariacia(nqbarra)

                if (aprovadoMW and aprovadoVW and aprovadoMNq and aprovadoVNq):

                    print(f'RESULTADOS DA SIMULACAO COM LAMB = {str(lamb)}, K = {str(k)}')
                    #print(f'media amostral = "+ str(np.mean(wbarra))
                    print(f'')
                    #item a
                    print(f'Tempo médio de espera em fila = {str(centerMW)}')
                    print(f'intervalo de confiança da espera em fila = {str(lowerMW)} ate {str(upperMW)}')
                    print(f'tamanho do intervalo de confiança do tempo médio = {str(upperMW-lowerMW)}')
                    print(f'')

                    #item b
                    print(f'Variancia média de espera em fila = {str(centerVW)}')
                    print(f'intervalo de confiança da variancia do tempo em fila = {str(lowerVW)} ate {str(upperVW)}')
                    print(f'')

                    #item c
                    print(f'Nq médio da fila = {str(centerMNq)}')
                    print(f'intervalo de confiança de Nq = {str(lowerMNq)} ate {str(upperMNq)}')
                    print(f'tamanho do intervalo de confianca do tempo medio = {str(upperMW-lowerMW)}')
                    print(f'')

                    #item d
                    print(f'Variancia média de Nq = {str(centerVW)}')
                    print(f'intervalo de confiança da variancia de Nq = {str(lowerVW)} ate {str(upperVW)}')
                    print(f'')

                    #fim da simulacao
                    print(f'Fim da simulação com lamb = {str(lamb)}, k = {str(k)}, tipo de fila = {disciplina}')
                    print(f'-------------------------------------')



                    #area de teste para prints de graficos para o Trabalho
                    #essa parte do codigo ficara comentada para nao gerar centenas de graficos especificos em todas as execucoes


                    #plt.plot(tempos[0:k])
                    #plt.show()

                    #plt.plot(pessoas_na_fila)
                    #plt.show()

                else:
                    #significa que a quantidade minima de eventos por rodada nao foi o suficiente para gerar os resultados esperados
                    #entao incrementamos a quantidade de rodadas minimas para a proxima bateria de testes, e como essa já nao é mais valida,
                    #os resultados com esse k nao sao mais interessantes
                    print(f'CONFIANÇA EXIGIDA NÃO FOI ATENDIDA, PULANDO PARA A PROXIMA ITERACAO COM K INCREMENTADO DE 100')
                    kmins.append(k+100)
                    print(f'NOVO VALOR DE K = {str(k+100)}')
                    
