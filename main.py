#!/usr/bin/env python3
import argparse
import random
from datetime import datetime

from controllers.calculadora import *
from controllers.estatisticasAmostrais import *
from models.evento import *
from models.cliente import *

parser = argparse.ArgumentParser(description='Simulação FCFS/LCFS')
parser.add_argument('disciplina', help='disciplina de atendimento (padrão FCFS)')
args = parser.parse_args()

if args.disciplina.lower() == "lcfs":
    disciplina = 'lcfs'
else:
    disciplina = 'fcfs'

class Simulador(object):
    def __init__(self, lamb, mu, k, n_rodadas, disciplina):
        self.transiente = True
        self.tx_chegada = lamb
        self.tx_servico = mu
        self.k_atual = k
        self.n_rodadas = n_rodadas
        self.disciplina = disciplina #FCFS ou LCFS
        self.tempo = -1.0
        self.servidor_ocupado = False
        self.rodada_atual = 1 #-1 para fase transiente

        ##### LISTAS #####
        self.eventos = [] #lista de eventos que vai comandar a ordem em que acontecem as chegadas e saídas
        self.fila_de_clientes = [] #lista que armazenará clientes até serem atendidos
        self.todos_clientes_atendidos = [] #lista de todos os clientes atendidos
        #self.qtdPessoasNaFilaPorRodada = [] #lista de pessoas na fila de espera por rodada
        self.E_W_por_rodada = [] #tempo médio gasto na fila de espera por rodada
        self.E_Nq_por_rodada = [] #tamanho médio da fila de espera por rodada
        self.clientes_atendidos_rodada = [] #lista de clientes completos por rodada
        
        self.sementesUsadas = [] #armazena sequencia de sementes usadas
        self.distanciaSementes = 0.0001 # Define distancia para sementes usadas.
        
        self.e_E_W = EstatisticasAmostrais()
        self.e_E_Nq = EstatisticasAmostrais()
        self.e_V_W = EstatisticasAmostrais()
        self.e_V_Nq = EstatisticasAmostrais()

        self.clientes_na_fila_evento_anterior = 0
        self.tempo_evento_anterior = 0.0
        self.tempo_inicio_rodada = 0.0
        self.area_clientes_tempo = 0 #cálculo incremental da área a cada chegada na fila e a cada entrada em serviço

        self.chegadaClientesRodada = 0

        self.somaW = 0.0

    def defineSemente(self, semente):
        random.seed(semente)

    def escolheSemente(self, sementesUsadas, distancia):
        newNumber = 0
        while newNumber == 0:
            newNumber = random.random()
            for number in sementesUsadas:
                if abs(newNumber - number) < distancia:
                    newNumber = 0
        return newNumber
        
    
    def simulaTempoExponencial(self, taxa):
        r = random.random()
        tempo = (-1.0 * math.log(r)) / (taxa + 0.0)
        return tempo

    
    def somaArea(self): #função para o cálculo de pessoas na fila
        self.area_clientes_tempo += (self.tempo - self.tempo_evento_anterior) * self.clientes_na_fila_evento_anterior

    def calculaNq(self): #função para calcular a quantidade média de pessoas na fila da mm1
        tempo_da_rodada = self.tempo - self.tempo_inicio_rodada
        #self.E_Nq_por_rodada.append(self.area_clientes_tempo/tempo_da_rodada)
        # chama funcao para adicionar valor para estatisticas
        if tempo_da_rodada == 0:
           self.e_E_Nq.adicionaValor(0)
        else :
            self.e_E_Nq.adicionaValor(self.area_clientes_tempo/tempo_da_rodada)

    def inserirEventoEmOrdem(self, evento): #insere e ordena
        self.eventos.append(evento)
        self.eventos = sorted(self.eventos, key=lambda evento: evento.tempo_evento)

    def geraEventoChegada(self, cliente):
        self.chegadaClientesRodada += 1
        tempo_evento = self.tempo + 1.0
        return Evento("evento_chegada", cliente, tempo_evento, self.rodada_atual)

    def geraEventoSaida(self, cliente):
        tempo_evento = self.tempo + 3.0
        return Evento("evento_saida", cliente, tempo_evento, self.rodada_atual)


    def adicionaE_WDaRodada(self):
        n = float(len(self.clientes_atendidos_rodada))
        # mudar para somar incrementalmente e dividir por len(clientes_atendidos)
        #tempos_de_fila = [cliente.tempoEmEspera() for cliente in self.clientes_atendidos_rodada]
        # chama funcao para adicionar valor para estatisticas 
        #self.E_W_por_rodada.append(np.sum(tempos_de_fila)/n)
        if n == 0: 
            self.e_E_W.adicionaValor(0)
        else:
            self.e_E_W.adicionaValor(self.somaW/n)
        #self.e_E_W.adicionaValor(np.sum(tempos_de_fila)/n)
        

    def iniciaProcesso(self):
        self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual))) #cria o 1º evento
        while self.rodada_atual < self.n_rodadas:
            if self.eventos:
                evento_atual = self.eventos.pop(0) #retira o primeiro elemento da lista mantendo a ordem cronológica
                self.clientes_na_fila_evento_anterior = len(self.fila_de_clientes)
                if evento_atual.tipo_de_evento == "evento_chegada": #testa para ver o tipo de evento que está sendo tratado
                    self.tempo = evento_atual.tempo_evento #atualiza o tempo global para o tempo em que o evento está acontecendo
                    print(f'instante: {self.tempo}')
                    evento_atual.cliente.tempo_chegada = self.tempo #cliente recebe seu tempo de chegada de acordo com o tempo que ocasionou a sua criação
                    self.fila_de_clientes.append(evento_atual.cliente) #adiciona o cliente a fila da MM1
                    print(f'cliente de chegada {evento_atual.cliente.tempo_chegada} entra na fila')
                    if self.chegadaClientesRodada < 3:
                        self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual))) #cria uma nova chegada de cliente na lista de eventos
                elif evento_atual.tipo_de_evento == "evento_saida": #se o evento nao é de entrada então ele é de saída
                    self.tempo = evento_atual.tempo_evento #atualiza o tempo global para o tempo em que o evento está acontecendo
                    print(f'instante: {self.tempo}')
                    evento_atual.cliente.tempo_termino_servico = self.tempo #cliente recebe seu tempo de saída de acordo com o tempo que ocasionou a sua saída
                    # incrementa variavel acumuladora do somatorio de todos os W dos clientes atendidos
                    self.somaW += evento_atual.cliente.tempoEmEspera()
                    
                    self.servidor_ocupado = False #servidor deixa de estar ocupado
                    self.todos_clientes_atendidos.append(evento_atual.cliente) #adicionando na lista de todos os clientes atendidos
                    self.clientes_atendidos_rodada.append(evento_atual.cliente) #adicionando a lista de clientes atendidos nesta rodada

                    print(f'cliente de chegada {evento_atual.cliente.tempo_chegada} sai na fila')

            self.somaArea() #cálculo da area de pessoas por tempo para ser utilizado para calcular E_Nq_por_rodada
            print('bla')
            self.tempo_evento_anterior = self.tempo #atualiza o valor do tempo do evento que acabou de acontecer
            #self.qtdPessoasNaFilaPorRodada.append(len(self.fila_de_clientes)) #armazena qtd de pessoas atual num vetor

            #Se o servidor estiver liberado e ainda existir alguém na fila
            if (not self.servidor_ocupado and len(self.fila_de_clientes) != 0): #então o servidor serve o próximo cliente
                if (self.disciplina == "fcfs"): #Na FCFS, clientes serão removidos pela esquerda, que entrou a mais tempo
                    cliente = self.fila_de_clientes.pop(0)
                elif (self.disciplina == "lcfs"): #Na LCFS, clientes serão removidos pela direita, que entrou a menos tempo
                    cliente = self.fila_de_clientes.pop()
                cliente.tempo_comeco_servico = self.tempo #atualiza o tempo em que o cliente entrou em serviço
                print(f'Cliente de chegada {cliente.tempo_chegada} entra em servico')
                self.inserirEventoEmOrdem(self.geraEventoSaida(cliente)) #gera o evento de saída que essa entrada em serviço irá ocasionar
                self.servidor_ocupado = True

            if ((self.tempo % 9) == 0 and self.tempo > 0):
                self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual)))
                print('agendar cliente para proxima rodada')
            
            if ((self.tempo % 10) == 0 and self.tempo > 0):
                self.calculaNq()
                print(f'clientes atendidos na rodada: {str(len(self.clientes_atendidos_rodada))}')
                print(f'fim da rodada: {self.rodada_atual}')
                self.adicionaE_WDaRodada()
                self.clientes_atendidos_rodada = [] #limpar os clientes da rodada
                self.area_clientes_tempo = 0
                self.somaW = 0.0
                self.chegadaClientesRodada = 0
                self.tempo_inicio_rodada = self.tempo
                self.rodada_atual += 1 #indo para próxima rodada
            

                


if __name__ == '__main__':
    #valores_rho = [0.2, 0.4, 0.6, 0.8, 0.9] #vetor de valores rho dado pelo enunciado
    valores_rho = [0.2]
    mu = 1
    k_min = [10000]
    n_rodadas = 3200
    inicioSim = datetime.now()
    print(f'Simulação com disciplina {disciplina.upper()}')

    for lamb in valores_rho:
        for k in k_min:
            s = Simulador(lamb, mu, k, n_rodadas, disciplina)
            c = Calculadora()

            s.iniciaProcesso()

            #E_Nq = s.E_Nq_por_rodada
            #E_W = s.E_W_por_rodada
            #tempos = [t.tempoEmEspera() for t in s.todos_clientes_atendidos]
            #pessoas_na_fila = s.qtdPessoasNaFilaPorRodada
            # Lista contendo valores analiticos.

            infM_W, supM_W, centroMW, okMW = c.ICMedia(s.e_E_W.get_muChapeu(), s.e_E_W.get_sigmaChapeu(),s.e_E_W.n)
            infM_Nq, supM_Nq, centroMNq, okMNq = c.ICMedia(s.e_E_Nq.get_muChapeu(),s.e_E_Nq.get_sigmaChapeu(),s.e_E_Nq.n)
            infV_W, supV_W, centroVW, okVW = c.ICVariancia(s.e_E_W.get_muChapeu(), s.e_E_W.get_sigmaChapeu(),s.e_E_W.n)
            infV_Nq, supV_Nq, centroVNq, okVNq = c.ICVariancia(s.e_E_Nq.get_muChapeu(),s.e_E_Nq.get_sigmaChapeu(),s.e_E_Nq.n)
            #infV_W, supV_W, centroVW, okVW = c.ICVarianciaIncremental(E_W)
            #infV_Nq, supV_Nq, centroVNq, okVNq = c.ICVarianciaIncremental(E_Nq)

            if (okMW and okVW and okMNq and okVNq):
                print(f'Resultados com lambda = {lamb}, k = {k}')
                print(f'Tempo médio de espera na fila = {centroMW}')
                print(f'I.C. de espera na fila = {infM_W} até {supM_W}')
                print(f'Tamanho do I.C. do tempo médio na fila = {supM_W-infM_W}')
                print(f'Variância média de espera na fila = {centroVW}')
                print(f'I.C. da variância do tempo na fila = {min(infV_W, supV_W)} até {max(infV_W, supV_W)}')
                print(f'Nq médio da fila = {centroMNq}')
                print(f'I.C. de Nq = {infM_Nq} até {supM_Nq}')
                print(f'Variância média de Nq = {centroVNq}')
                print(f'I.C. da variância de Nq = {min(infV_Nq, supV_Nq)} até {max(infV_Nq, supV_Nq)}')
                print(f'proxima semente: {random.random()}')

                #c.plotGrafico(len(E_Nq[:500]), E_Nq[:500], disciplina, "rodadas", "E_Nq", disciplina + "1_" + str(lamb))
                #c.plotGrafico(n_rodadas, E_Nq, disciplina, "rodadas", "E_Nq", disciplina + "1_" + str(lamb))
                #c.plotGrafico(n_rodadas, E_W, disciplina, "rodadas", "E_W", disciplina + "2_" + str(lamb))
                #c.myPlot(n_rodadas, pessoas_na_fila)
            else:
                print(f'K não satisfatório, incrementando-o em 100 para a próxima iteração')
                k_min.append(k+100)
                print(f'Novo valor de k = {k_min}')
    print(f'------ Tempo total de simulação: {(datetime.now() - inicioSim)} ------')
