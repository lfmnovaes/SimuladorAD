#!/usr/bin/env python3

import argparse
import random
from datetime import datetime

from controllers.calculadora import *
from models.evento import *
from models.cliente import *

parser = argparse.ArgumentParser(description='Simulação FCFS/LCFS')
parser.add_argument('disciplina', help='disciplina de atendimento (padrão FCFS)')
args = parser.parse_args()

if (args.disciplina.lower() == "lcfs"):
    print(f'Executando com disciplina LCFS')
    disciplina = 'lcfs'
else:
    print(f'Executando com disciplina FCFS')
    disciplina = 'fcfs'

class Simulador(object):
    def __init__(self, lamb, mu, k, n_rodadas, disciplina):
        self.transiente = True
        self.tx_chegada = lamb
        self.tx_servico = mu
        self.min_k = k
        self.n_rodadas = n_rodadas
        self.disciplina = disciplina #FCFS ou LCFS
        self.tempo = 0.0
        self.servidor_ocupado = False
        self.rodada_atual = -1 #-1 para fase transiente

        ##### LISTAS #####
        self.lista_de_eventos = [] #lista de eventos que vai comandar a ordem em que acontecem as chegadas e saídas
        self.fila_de_clientes = [] #lista que armazenará clientes até serem atendidos
        self.todos_clientes_atendidos = [] #lista de todos os clientes atendidos
        self.qtt_pessoas_fila_por_rodada = [] #lista de pessoas na fila de espera por rodada
        self.E_W_por_rodada = [] #tempo médio gasto na fila de espera por rodada
        self.E_Nq_por_rodada = [] #tamanho médio da fila de espera por rodada
        self.clientes_na_fila_evento_anterior = 0
        self.tempo_evento_anterior = 0.0
        self.tempo_inicio_rodada = 0.0
        self.area_clientes_tempo = 0 #cálculo incremental da área a cada chegada na fila e a cada entrada em serviço
        self.clientes_atendidos_rodada = [] #lista de clientes completos por rodada

    def simulaTempoExponencial(self, taxa):
        r = random.random()
        tempo = (-1.0 * math.log(r)) / (taxa + 0.0)
        return tempo

    def somaArea(self): #função para o cálculo de pessoas na fila
        self.area_clientes_tempo += (self.tempo - self.tempo_evento_anterior) * self.clientes_na_fila_evento_anterior

    def calculaNq(self): #função para calcular a quantidade média de pessoas na fila da mm1
        tempo_da_rodada = self.tempo - self.tempo_inicio_rodada
        self.E_Nq_por_rodada.append(self.area_clientes_tempo/tempo_da_rodada)

    def inserirEventoEmOrdem(self, evento):
        self.lista_de_eventos.append(evento)
        self.lista_de_eventos = sorted(self.lista_de_eventos, key=lambda evento: evento.tempo_evento)

    def geraEventoChegada(self, cliente):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_chegada)
        return Evento("evento_chegada", cliente, tempo_evento, self.rodada_atual)

    def geraEventoSaida(self, cliente):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_servico)
        return Evento("evento_saida", cliente, tempo_evento, self.rodada_atual)

    def testeFaseTransiente(self):
        tStudent = 1.645 #T-student para mais de 120 amostras
        n = len(self.clientes_atendidos_rodada) #qtt de amostras
        tempos_de_fila = [cliente.tempoEmEspera() for cliente in self.clientes_atendidos_rodada]
        mean = np.sum(tempos_de_fila)/n #média amostral
        #variância amostral = SUM((Media - Media Amostral)^2) = S^2
        s = math.sqrt(np.sum([(float(element) - float(mean))**2 for element in tempos_de_fila])/(n-1.0))
        lower = mean - (tStudent*(s/math.sqrt(n))) #cálculo do I.C. pela T-student
        upper = mean + (tStudent*(s/math.sqrt(n)))
        center = lower + (upper - lower)/2
        if center/10 < (upper - lower):
            self.transiente = False

    def adicionaE_WDaRodada(self):
        n = float(len(self.clientes_atendidos_rodada))
        tempos_de_fila = [cliente.tempoEmEspera() for cliente in self.clientes_atendidos_rodada]
        self.E_W_por_rodada.append(np.sum(tempos_de_fila)/n)

    def iniciaProcesso(self):
        self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual))) #cria o 1º evento
        while self.rodada_atual < self.n_rodadas:
            evento_atual = self.lista_de_eventos.pop(0) #retira o primeiro elemento da lista mantendo a ordem cronológica
            self.clientes_na_fila_evento_anterior = len(self.fila_de_clientes)
            if evento_atual.tipo_de_evento == "evento_chegada": #testa para ver o tipo de evento que está sendo tratado
                self.tempo = evento_atual.tempo_evento #atualiza o tempo global para o tempo em que o evento está acontecendo
                evento_atual.cliente.tempo_chegada = self.tempo #cliente recebe seu tempo de chegada de acordo com o tempo que ocasionou a sua criação
                self.fila_de_clientes.append(evento_atual.cliente) #adiciona o cliente a fila da MM1
                self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual))) #cria uma nova chegada de cliente na lista de eventos
            elif evento_atual.tipo_de_evento == "evento_saida": #se o evento nao é de entrada, entao ele é de saída
                self.tempo = evento_atual.tempo_evento #atualiza o tempo global para o tempo em que o evento está acontecendo
                evento_atual.cliente.tempo_termino_servico = self.tempo #cliente recebe seu tempo de saída de acordo com o tempo que ocasionou a sua saída
                self.servidor_ocupado = False #servidor deixa de estar ocupado
                self.todos_clientes_atendidos.append(evento_atual.cliente) #adicionando na lista de todos os clientes atendidos
                self.clientes_atendidos_rodada.append(evento_atual.cliente) #adicionando a lista de clientes atendidos nesta rodada

            self.somaArea() #cálculo da area de pessoas por tempo para ser utilizado para calcular E_Nq_por_rodada
            self.tempo_evento_anterior = self.tempo #atualiza o valor do tempo do evento que acabou de acontecer
            self.qtt_pessoas_fila_por_rodada.append(len(self.fila_de_clientes)) #armazena qtt de pessoas atual num vetor

            #Se o servidor estiver liberado e ainda existir alguém na fila
            if (not self.servidor_ocupado and len(self.fila_de_clientes) != 0): #então o servidor serve o próximo cliente
                if (self.disciplina == "fcfs"): #Na FCFS, clientes serão removidos pela esquerda, que entrou a mais tempo
                    cliente = self.fila_de_clientes.pop(0)
                elif (self.disciplina == "lcfs"): #Na LCFS, clientes serão removidos pela direita, que entrou a menos tempo
                    cliente = self.fila_de_clientes.pop()
                cliente.tempo_comeco_servico = self.tempo #atualiza o tempo em que o cliente entrou em serviço
                self.inserirEventoEmOrdem(self.geraEventoSaida(cliente)) #gera o evento de saída que essa entrada em serviço irá ocasionar
                self.servidor_ocupado = True

            if len(self.clientes_atendidos_rodada) >= self.min_k:
                if self.transiente:
                    self.testeFaseTransiente()
                    #começa a fase transiente até convergir, com limite de 10 * o tamanho da rodada
                    if not self.transiente or len(self.clientes_atendidos_rodada) > (10*self.min_k):
                        self.rodada_atual += 1
                        self.clientes_atendidos_rodada = []
                        self.tempo_inicio_rodada = self.tempo
                        self.area_clientes_tempo = 0
                else:
                    self.calculaNq()
                    #print(f'clientes atendidos na rodada: {str(len(self.clientes_atendidos_rodada}))}')
                    self.adicionaE_WDaRodada()
                    self.clientes_atendidos_rodada = [] #limpar os clientes da rodada
                    self.area_clientes_tempo = 0
                    self.tempo_inicio_rodada = self.tempo
                    self.rodada_atual += 1 #indo para próxima rodada

if __name__ == '__main__':
    #valores_rho = [0.2, 0.4, 0.6, 0.8, 0.9] #vetor de valores rho dado pelo enunciado
    valores_rho = [0.9]
    mu = 1
    kmins = [150]
    n_rodadas = 3200
    inicioSim = datetime.now()

    for lamb in valores_rho:
        for k in kmins:
            s = Simulador(lamb, mu, k, n_rodadas, disciplina)
            c = Calculadora()
            s.iniciaProcesso()

            E_Nq = s.E_Nq_por_rodada
            E_W = s.E_W_por_rodada

            tempos = [t.tempoEmEspera() for t in s.todos_clientes_atendidos]
            pessoas_na_fila = s.qtt_pessoas_fila_por_rodada

            lowerMW, upperMW, centerMW, aprovadoMW = c.ICMedia(E_W)
            lowerMNq, upperMNq, centerMNq, aprovadoMNq = c.ICMedia(E_Nq)
            lowerVW, upperVW, centerVW, aprovadoVW = c.ICDaVariancia(E_W)
            lowerVNq, upperVNq, centerVNq, aprovadoVNq = c.ICDaVariancia(E_Nq)

            if (aprovadoMW and aprovadoVW and aprovadoMNq and aprovadoVNq):
                print(f'Resultados da simulação com lambda = {str(lamb)}, k = {str(k)} e disciplina = {disciplina}')
                print(f'')
                print(f'Tempo médio de espera em fila = {str(centerMW)}')
                print(f'I.C. de espera em fila = {str(lowerMW)} até {str(upperMW)}')
                print(f'Tamanho do I.C. do tempo médio = {str(upperMW-lowerMW)}')
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
                print(f'------ Tempo de Simulação: {(datetime.now() - inicioSim)} ------')

                #c.plotGrafico(x, y, x_legenda, y_legenda)
                c.plotGrafico(n_rodadas, E_Nq, disciplina, "rodadas", "E_Nq", disciplina + "1_" + str(lamb))
                c.plotGrafico(n_rodadas, E_W, disciplina, "rodadas", "E_W", disciplina + "2_" + str(lamb))

                #print(f'tempos: {len(tempos)} - e_nq: {len(E_Nq)} - e_w: {len(E_W)}')
                #print(f'tempos: {tempos[:10]} - e_nq: {E_Nq[:10]} - e_w: {E_W[:10]}')
            else:
                print(f'confiança não foi obtida, incrementando k em 100 na próxima iteração')
                kmins.append(k+100)
                print(f'novo valor de k = {str(k+100)}')
