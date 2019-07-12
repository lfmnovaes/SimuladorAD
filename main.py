#!/usr/bin/env python3

import argparse
import datetime
#import math
import random
#from scipy import stats
#from scipy.stats import chi2
#import matplotlib
#import matplotlib.pyplot as plt
#import numpy as np

from controllers.calculadora import *
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
        self.disciplina = disciplina    #FCFS ou LCFS
        self.tempo = 0.0
        self.servidor_ocupado = False
        self.rodada_atual = -1          #-1 para fase transiente

        ##### LISTAS #####
        #lista de eventos que vai comandar a ordem em que acontecem as chegadas e saidas
        self.lista_de_eventos = []

        #fila da MM1, que terao clientes esperando para serem atendidos
        self.fila_de_clientes = []

        #lista para salvar dados dos clientes para a geracao de graficos
        self.todos_clientes_atendidos = []
        self.qtd_total_pessoas_fila = []

        #listas que irao guardar metricas
        self.E_W_por_rodada = []

        #variaveis necessarias para o calculo de nq
        self.E_Nq_por_rodada = []
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
        # podemos utilizar dessa forma otimizada, pois tanto 1-r, quanto r sao numeros aleatorios de 0 a 1, dessa forma,
        # economizamos 1 operacao de subtracao por numero gerado
        tempo = (-1.0 * math.log(r)) / (taxa + 0.0)
        return tempo

    #funcao auxiliar para o calculo de pessoas na fila
    def somaArea(self):
        self.area_clientes_tempo += (self.tempo - self.tempo_evento_anterior ) * self.clientes_na_fila_evento_anterior

    #funcao para calcular a quantidade media de pessoas na fila da mm1
    def calculaNq(self):
        tempo_da_rodada = self.tempo - self.tempo_inicio_rodada
        self.E_Nq_por_rodada.append(self.area_clientes_tempo/tempo_da_rodada)

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
        #variância amostral = SUM((Media - Media Amostral)^2) = S^2
        s = math.sqrt(np.sum([(float(element) - float(mean))**2 for element in tempos_de_fila])/(n-1.0))
        #calculo do I.C. pela T-student
        lower = mean - (percentil*(s/math.sqrt(n)))
        upper = mean + (percentil*(s/math.sqrt(n)))
        center = lower + (upper - lower)/2
        if center/10 < (upper - lower):
            self.transiente = False

    def adicionaE_WDaRodada(self):
        n = float(len(self.clientes_atendidos_rodada))
        tempos_de_fila = [cliente.tempoEmEspera() for cliente in self.clientes_atendidos_rodada]
        self.E_W_por_rodada.append(np.sum(tempos_de_fila)/n)

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

            #faz calculo da area de pessoas por tempo para ser utilizado para calcular E_Nq_por_rodada
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
                    self.testeFaseTransiente()
                    #caso chegue ao fim da fase transiente, entao comecamos a rodada 0
                    #estarei estabelecendo um fim forcado para a fase transiente caso os tempos nao consigam convergir!
                    #esse tempo será o equivalente a 10 vezes o tamanho da rodada
                    if not self.transiente or len(self.clientes_atendidos_rodada) > (10*self.min_k):
                        self.rodada_atual += 1
                        self.clientes_atendidos_rodada = []
                        self.tempo_inicio_rodada = self.tempo
                        self.area_clientes_tempo = 0
                else:
                    #gera metricas e estatisticas
                    self.calculaNq()
                    #print "clientes atendidos na rodada: "+str(len(self.clientes_atendidos_rodada))
                    self.adicionaE_WDaRodada()

                    # limpando os clientes atendidos nesta rodada
                    self.clientes_atendidos_rodada = []
                    self.area_clientes_tempo = 0
                    self.tempo_inicio_rodada = self.tempo

                    # proxima rodada
                    #print "rodada: " + str(self.rodada_atual)
                    self.rodada_atual += 1

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
                #self, tx_chegada: float, tx_servico: float, k: int, n: int, disciplina: int, IC: float, precisao: float, utilizacao: float):
                s = Simulador(lamb, mu, k, n_rodadas, disciplina)
                c = Calculadora()
                s.iniciaProcesso()

                E_Nq = s.E_Nq_por_rodada
                E_W = s.E_W_por_rodada

                tempos = [t.tempoEmEspera() for t in s.todos_clientes_atendidos]
                pessoas_na_fila = s.qtd_total_pessoas_fila

                lowerMW, upperMW, centerMW, aprovadoMW = c.ICDaMedia(E_W)
                lowerMNq, upperMNq, centerMNq, aprovadoMNq = c.ICDaMedia(E_Nq)
                lowerVW, upperVW, centerVW, aprovadoVW = c.ICDaVariacia(E_W)
                lowerVNq, upperVNq, centerVNq, aprovadoVNq = c.ICDaVariacia(E_Nq)

                if (aprovadoMW and aprovadoVW and aprovadoMNq and aprovadoVNq):

                    print(f'Resultados da simulação com lambda = {str(lamb)} e k = {str(k)}')
                    #print(f'media amostral = {str(np.mean(E_W)}')
                    print(f'')
                    print(f'Tempo médio de espera em fila = {str(centerMW)}')
                    print(f'I.C. da espera em fila = {str(lowerMW)} até {str(upperMW)}')
                    print(f'tamanho do I.C. do tempo médio = {str(upperMW-lowerMW)}')
                    print(f'')
                    print(f'Variância média de espera em fila = {str(centerVW)}')
                    print(f'I.C. da variância do tempo em fila = {str(lowerVW)} ate {str(upperVW)}')
                    print(f'')
                    print(f'Nq médio da fila = {str(centerMNq)}')
                    print(f'I.C. de Nq = {str(lowerMNq)} até {str(upperMNq)}')
                    print(f'')
                    print(f'Variância média de Nq = {str(centerVW)}')
                    print(f'I.C. da variância de Nq = {str(lowerVW)} ate {str(upperVW)}')
                    print(f'')

                    #fim da simulacao
                    print(f'Fim da simulação com lamb = {str(lamb)}, k = {str(k)}, disciplina = {disciplina}')
                    print(f'-------------------------------------')

                    #c.plotGrafico(x, y, x_legenda, y_legenda)
                    c.plotGrafico(n_rodadas, E_Nq, "rodadas", "E_Nq", "plot1")
                    c.plotGrafico(n_rodadas, E_W, "rodadas", "E_W", "plot2")

                    #print(f'tempos: {len(tempos)} - e_nq: {len(E_Nq)} - e_w: {len(E_W)}')
                    #print(f'tempos: {tempos[:10]} - e_nq: {E_Nq[:10]} - e_w: {E_W[:10]}')

                else:
                    #significa que a quantidade minima de eventos por rodada nao foi o suficiente para gerar os resultados esperados
                    #entao incrementamos a quantidade de rodadas minimas para a proxima bateria de testes, e como essa já nao é mais valida,
                    #os resultados com esse k nao sao mais interessantes
                    print(f'CONFIANÇA EXIGIDA NÃO FOI ATENDIDA, PULANDO PARA A PROXIMA ITERACAO COM K INCREMENTADO DE 100')
                    kmins.append(k+100)
                    print(f'NOVO VALOR DE K = {str(k+100)}')
