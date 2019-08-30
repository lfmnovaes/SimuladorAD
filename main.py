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
parser.add_argument('lambd', type=float, default=0.2, help='lambda')
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
        self.tempo = 0.0
        self.servidor_ocupado = False
        self.rodada_atual = -1 #-1 para fase transiente

        ##### LISTAS #####
        self.eventos = [] #lista de eventos que vai comandar a ordem em que acontecem as chegadas e saídas
        self.fila_de_clientes = [] #lista que armazenará clientes até serem atendidos
        #self.todos_clientes_atendidos = [] #lista de todos os clientes atendidos
        self.qtdPessoasNaFilaPorRodada = [] #lista de pessoas na fila de espera por rodada
        self.E_W_por_rodada = [] #tempo médio gasto na fila de espera por rodada
        self.E_Nq_por_rodada = [] #tamanho médio da fila de espera por rodada
        #self.clientes_atendidos_rodada = [] #lista de clientes completos por rodada
        # P_Nq e a estrutura que armazena uma quantidade de clientes na fila e o intervalo de tempo que a fila permanexe com essa quantidade
        # Essa estrutura sera importante para gerar a pmf de Nq e conseguentemente calcular V(Nq)
        #self.P_Nq = [0 for i in range(k)] 
        #self.V_W = []
        #self.VW_rodada =[]
        #self.VNq_rodada = []

        
        #self.sementesUsadas = [] #armazena sequencia de sementes usadas
        #self.distanciaSementes = 0.0001 # Define distancia para sementes usadas.
        
        self.e_E_W = EstatisticasAmostrais()
        self.e_E_Nq = EstatisticasAmostrais()
        self.e_V_W = EstatisticasAmostrais()
        self.e_V_Nq = EstatisticasAmostrais()
        self.e_Wij = EstatisticasAmostrais() # classes com metodos para calcular media e variancia na fase transiente e dntro de cada rodada
        self.e_Nqij = EstatisticasAmostrais()

        self.clientes_na_fila_evento_anterior = 0
        self.tempo_evento_anterior = 0.0
        self.tempo_inicio_rodada = 0.0
        self.area_clientes_tempo = 0 #cálculo incremental da área a cada chegada na fila e a cada entrada em serviço
        self.area_clientes_tempoQuad = 0

        self.somaW = 0.0
        #Incrementa conforme os cliente forem atendidos
        # (mais rapido que percorrer lista self.clientes_atendidos_rodada = [])
        self.clientes_atendidos_rodada_inc = 0  
        self.r =  0.8067697303247167

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
        self.area_clientes_tempo += ((self.tempo - self.tempo_evento_anterior) * self.clientes_na_fila_evento_anterior)
        self.area_clientes_tempoQuad += ((self.tempo - self.tempo_evento_anterior) * self.clientes_na_fila_evento_anterior*self.clientes_na_fila_evento_anterior)

    def calculaNq(self): #função para calcular a quantidade média de pessoas na fila da mm1
        soma = somQuad = 0
        E_Nq = E_Nq_2 = 0.0
        tempo_da_rodada = self.tempo - self.tempo_inicio_rodada
        # chama funcao para adicionar valor para estatisticas
        E_Nq = self.area_clientes_tempo/tempo_da_rodada
        E_Nq_2 = self.area_clientes_tempoQuad/tempo_da_rodada
        VNqi = E_Nq_2 - E_Nq**2
        self.e_E_Nq.adicionaValor(E_Nq)
        self.e_V_Nq.adicionaValor(VNqi)
        #self.VNq_rodada.append(VNqi)

    def inserirEventoEmOrdem(self, evento): #insere e ordena
        self.eventos.append(evento)
        self.eventos = sorted(self.eventos, key=lambda evento: evento.tempo_evento)

    def geraEventoChegada(self, cliente):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_chegada)
        return Evento("evento_chegada", cliente, tempo_evento, self.rodada_atual)

    def geraEventoSaida(self, cliente):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_servico)
        return Evento("evento_saida", cliente, tempo_evento, self.rodada_atual)

    def testeFaseTransiente(self, est_metrica):
        n = est_metrica.n
        tStudent = c.tstudent(0.95, n-1)
        # Média amostral
        mean = est_metrica.get_muChapeu()
        #print(f'mean = {mean}')
        # desvio padrao 
        s = math.sqrt(est_metrica.get_sigmaChapeu())
        # cálculo do I.C. pela T-student
        inferior = mean - (tStudent*(s/math.sqrt(n)))
        superior = mean + (tStudent*(s/math.sqrt(n)))
        centro = inferior + (superior - inferior)/2
        #precisao_tstudent = tStudent*(s/mean*math.sqrt(n))
        precisao_tstudent = (superior - inferior) / (superior + inferior)
        '''
        print(f'k:{self.clientes_atendidos_rodada_inc}; n:{n};')
        print(f'media de sigmaChapeu^2: {mean}; precTStudent: {precisao_tstudent}')
        print(f'inf:{inferior}; sup:{superior}; centro:{centro}')
        '''
        # precisao = 0.0045 ?
        if precisao_tstudent < 0.01:
            self.transiente = False

    def adicionaE_WDaRodada(self):
        k = self.clientes_atendidos_rodada_inc
        VWi = self.e_Wij.get_sigmaChapeu()
        # chama funcao para adicionar media dos k clientes da rodada na classe que calcula de forma incremental os estimadores da media e da variancia 
        self.e_E_W.adicionaValor(self.e_Wij.get_muChapeu())
        # chama funcao para adicionar a variancia dos tempos de espera dos k clientes da rodada. 
        # Essa classe fornece a media dessas variancias para calculo da IC da variancia posteriormente
        
        self.e_V_W.adicionaValor(VWi)
        #self.VW_rodada.append(VWi)
        
    def iniciaProcesso(self):
        '''
        r = self.escolheSemente(self.sementesUsadas, self.distanciaSementes)
        self.sementesUsadas.append(r) # Define primeira semente. A cada rodada
        '''
        #self.defineSemente(self.r)
        
        self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual))) #cria o 1º evento
        while self.rodada_atual < self.n_rodadas:
            evento_atual = self.eventos.pop(0) #retira o primeiro elemento da lista mantendo a ordem cronológica
            self.clientes_na_fila_evento_anterior = len(self.fila_de_clientes)
            if evento_atual.tipo_de_evento == "evento_chegada": #testa para ver o tipo de evento que está sendo tratado
                self.tempo = evento_atual.tempo_evento #atualiza o tempo global para o tempo em que o evento está acontecendo
                evento_atual.cliente.tempo_chegada = self.tempo #cliente recebe seu tempo de chegada de acordo com o tempo que ocasionou a sua criação
                self.fila_de_clientes.append(evento_atual.cliente) #adiciona o cliente a fila da MM1
                self.inserirEventoEmOrdem(self.geraEventoChegada(Cliente(self.rodada_atual))) #cria uma nova chegada de cliente na lista de eventos
            elif evento_atual.tipo_de_evento == "evento_saida": #se o evento nao é de entrada então ele é de saída
                self.tempo = evento_atual.tempo_evento #atualiza o tempo global para o tempo em que o evento está acontecendo
                evento_atual.cliente.tempo_termino_servico = self.tempo #cliente recebe seu tempo de saída de acordo com o tempo que ocasionou a sua saída
                # incrementa variavel acumuladora do somatorio de todos os W dos clientes atendidos
                self.e_Wij.adicionaValor(evento_atual.cliente.tempoEmEspera())
                if self.transiente:
                    self.e_V_W.adicionaValor(self.e_Wij.get_sigmaChapeu())
                    #self.V_W.append(self.e_Wij.get_sigmaChapeu())

               
                self.servidor_ocupado = False #servidor deixa de estar ocupado
                #self.todos_clientes_atendidos.append(evento_atual.cliente) #adicionando na lista de todos os clientes atendidos
                #self.clientes_atendidos_rodada.append(evento_atual.cliente) #adicionando a lista de clientes atendidos nesta rodada
                self.clientes_atendidos_rodada_inc += 1

            self.somaArea() #cálculo da area de pessoas por tempo para ser utilizado para calcular E_Nq_por_rodada
            self.tempo_evento_anterior = self.tempo #atualiza o valor do tempo do evento que acabou de acontecer
            self.qtdPessoasNaFilaPorRodada.append(len(self.fila_de_clientes)) #armazena qtd de pessoas atual num vetor

            #Se o servidor estiver liberado e ainda existir alguém na fila
            if (not self.servidor_ocupado and len(self.fila_de_clientes) != 0): #então o servidor serve o próximo cliente
                if (self.disciplina == "fcfs"): #Na FCFS, clientes serão removidos pela esquerda, que entrou a mais tempo
                    cliente = self.fila_de_clientes.pop(0)
                elif (self.disciplina == "lcfs"): #Na LCFS, clientes serão removidos pela direita, que entrou a menos tempo
                    cliente = self.fila_de_clientes.pop()
                cliente.tempo_comeco_servico = self.tempo #atualiza o tempo em que o cliente entrou em serviço
                self.inserirEventoEmOrdem(self.geraEventoSaida(cliente)) #gera o evento de saída que essa entrada em serviço irá ocasionar
                self.servidor_ocupado = True

            if self.clientes_atendidos_rodada_inc >= (self.k_atual):
                if self.transiente :
                    #if self.clientes_atendidos_rodada_inc >= (self.k_atual*5):
                    self.testeFaseTransiente(self.e_V_W)
                #começa a fase transiente até convergir, com limite de 10 vezes o tamanho da rodada
                #if not self.transiente or self.clientes_atendidos_rodada_inc > (10*self.k_atual):
                    if not self.transiente:
                        self.rodada_atual += 1
                        self.tempo_inicio_rodada = self.tempo
                        self.area_clientes_tempo = 0
                        self.area_clientes_tempoQuad = 0
                        self.somaW = 0.0
                        self.clientes_atendidos_rodada_inc = 0
                        self.e_Wij.zeraValores()
                        self.e_V_W.zeraValores()

                else:
                    self.calculaNq()
                    self.adicionaE_WDaRodada()
                    #print(f'sigmaChapeuQuad: {self.e_V_Nq.get_sigmaChapeu()}')
                    self.area_clientes_tempo = 0
                    self.area_clientes_tempoQuad = 0
                    self.somaW = 0.0
                    self.clientes_atendidos_rodada_inc = 0
                    self.e_Wij.zeraValores()
                    self.tempo_inicio_rodada = self.tempo
                    self.rodada_atual += 1 #indo para próxima rodada

if __name__ == '__main__':
    #valores_rho = [0.2, 0.4, 0.6, 0.8, 0.9] #vetor de valores rho dado pelo enunciado
    valores_rho = []
    valores_rho.append(float(args.lambd))
    k_inicial = 100
    mu = 1
    n_rodadas = 3200
    #define semente de execucao
    
    # FCFS: semente utilizada: 0.6914235947085864; proxima semente: 0.8159484329221927
    # LCFS: semente utilizada: 0.6914235947085864; proxima semente: 0.13793458642458434
    # Com graphs   FCFS: semente utilizada: 0.6914235947085864; prox.    0.7987046076819015
    # Com graphs   LCFS: semente utilizada: 0.6914235947085864; proxima semente: 0.45547483774307906
    r = 0.45547483774307906
    random.seed(r)
    inicioSim = datetime.now()

    print(f'Simulação com disciplina {disciplina.upper()}')

    for lamb in valores_rho:
        k_min =  [k_inicial]
        okMW = okMNq = okVW = okVNq = sobreposicaoVW = sobreposicaoVNq = False
        k_min_EW = k_min_VW = k_min_ENq = k_min_VNq = '-'

        # Inicializar Listas para armazenar valores de convergencia das ICs das Variancias
        chi2Inf_VW = []
        chi2Sup_VW = []
        chi2Cent_VW = []
        tInf_VW = []
        tSup_VW = []
        tCent_VW = []
        k_VW = []

        chi2Inf_VNq = []
        chi2Sup_VNq = []
        chi2Cent_VNq = []
        tInf_VNq = []
        tSup_VNq = []
        tCent_VNq = []
        k_VNq = []

        for k in k_min:
            s = Simulador(lamb, mu, k, n_rodadas, disciplina)
            c = Calculadora()

            s.iniciaProcesso()

            # Lista contendo valores analiticos.
            if disciplina == "lcfs":
                v_w_Analit = (2*lamb - lamb**2 + lamb**3)/(1-lamb)**3 
            elif disciplina == "fcfs":        
                v_w_Analit = (2*lamb - lamb**2)/(1-lamb)**2

            e_w_Analit = lamb/(1-lamb)
            v_Nq_Analit = (lamb**2 + lamb**3 - lamb**4)/(1-lamb)**2
            e_Nq_Analit = lamb**2/(1-lamb)

            if not okMW:
                infM_W, supM_W, centroMW, okMW, precE_W = c.ICMedia(s.e_E_W.get_muChapeu(), s.e_E_W.get_sigmaChapeu(),n_rodadas, e_w_Analit)
                if okMW:
                    k_min_EW = k
            if not okMNq:
                infM_Nq, supM_Nq, centroMNq, okMNq, precE_Nq = c.ICMedia(s.e_E_Nq.get_muChapeu(),s.e_E_Nq.get_sigmaChapeu(),n_rodadas, e_Nq_Analit)
                if okMNq:
                    k_min_ENq = k                
            if not okVW:
                infV_W, supV_W, centroVW, okVW, precV_W, centroVWT, precV_WT, infV_WT, supV_WT, sobreposicaoVW = c.ICVariancia(s.e_V_W.get_muChapeu(), s.e_V_W.get_sigmaChapeu(),n_rodadas, v_w_Analit)
                chi2Inf_VW.append(infV_W)
                chi2Sup_VW.append(supV_W)
                chi2Cent_VW.append(centroVW)
                tInf_VW.append(infV_WT)
                tSup_VW.append(supV_WT)
                tCent_VW.append(centroVWT)
                k_VW.append(k)
                if okVW:
                    k_min_VW = k                
            if not okVNq:    
                infV_Nq, supV_Nq, centroVNq, okVNq, precV_Nq, centroVNqT, precV_NqT, infV_NqT, supV_NqT, sobreposicaoVNq = c.ICVariancia(s.e_V_Nq.get_muChapeu(),s.e_V_Nq.get_sigmaChapeu(),n_rodadas, v_Nq_Analit)
                chi2Inf_VNq.append(infV_Nq)
                chi2Sup_VNq.append(supV_Nq)
                chi2Cent_VNq.append(centroVNq)
                tInf_VNq.append(infV_NqT)
                tSup_VNq.append(supV_NqT)
                tCent_VNq.append(centroVNqT)
                k_VNq.append(k)
                if okVNq:
                    k_min_VNq = k                


            #print(okMW, okVW, okMNq, okVNq)

            print(f'Resultados com lambda = {lamb}, k = {k}, Disciplina: {disciplina}')
            print('---//---')
            print("E[W] centro do IC = %.4f" % (centroMW))
            print("I.C. de E[W] = %.4f ate %.4f" % (infM_W,supM_W))
            print("E[W] analitico = %.4f" % (e_w_Analit))
            print("Precisao do I.C. do E[W] = %.4f" % (precE_W))
            print(f'K min: {k_min_EW}')
            print('---//---')
            print("V(W) = %.4f" % (centroVW))
            print("I.C. de V(W) = %.4f ate %.4f" % (infV_W, supV_W))
            print("V(W) analitico = %.4f" % (v_w_Analit))
            print("V(W)[ centro t-Student ] = %.4f" % (centroVWT))
            print("I.C. de V(W) t-Student = %.4f ate %.4f" % (infV_WT, supV_WT))
            print("Precisao do IC de V(W) = %.4f" % (precV_W))
            print("Precisao do IC de V(W) t-Student = %.4f" % (precV_WT))
            print(f'Houve sobreposicao de ICs: {sobreposicaoVW}')
            print(f'K min: {k_min_VW}')
            print('---//---')            
            print("E[Nq] = %.4f" % (centroMNq))            
            print("I.C. de E[Nq] = %.4f ate %.4f" % (infM_Nq, supM_Nq))
            print("E[Nq] analitico = %.4f" % (e_Nq_Analit))
            print("Precisao do I.C. de E[Nq] = %.4f" % (precE_Nq))
            print(f'K min: {k_min_ENq}')
            print('---//---')
            print("V(Nq) = %.4f" % (centroVNq))
            print("I.C. de V(Nq) = %.4f ate %.4f" % (infV_Nq, supV_Nq))
            print("V(Nq) analitico = %.4f" % (v_Nq_Analit))
            print("Precisao do I.C. de V(Nq) = %.4f" % (precV_Nq))            
            print("V(Nq)[ centro t-Student ] = %.4f" % (centroVNqT))
            print("I.C. de V(Nq) t-Student = %.4f ate %.4f" % (infV_NqT, supV_NqT))
            print("Precisao do IC de V(Nq) t-Student = %.4f" % (precV_NqT))            
            print(f'Houve sobreposicao de ICs: {sobreposicaoVNq}')
            print(f'K min: {k_min_VNq}')

            print(f'------ Tempo parcial de simulação: {(datetime.now() - inicioSim)} ------')
            
            #print(okMW, okVW, okMNq, okVNq)
            if (okMW==True and okVW==True and okMNq==True and okVNq==True):
                print('Novo Lambda')
        
            else:
                print(f'K não satisfatório, incrementando-o em 100 para a próxima iteração')
                k_min.append(k+100)
                #print(f'Novo valor de k = {k_min}')
    
        xW = len(k_VW)
        xNq = len(k_VNq)
        
        y1W = chi2Sup_VW
        y2W = chi2Cent_VW
        y3W = chi2Inf_VW

        yt1W = tSup_VW
        yt2W = tCent_VW
        yt3W = tInf_VW

        y1Nq = chi2Sup_VNq
        y2Nq = chi2Cent_VNq
        y3Nq = chi2Inf_VNq

        yt1Nq = tSup_VNq
        yt2Nq = tCent_VNq
        y3tNq = tInf_VNq

        
        saida1 = disciplina+"_"+str(lamb)+'_vW2ndSeed'
        saida2 = disciplina+"_"+str(lamb)+'_vNq2ndSeed'
        f1, ax1 = plt.subplots() 
        #plt.subplot(2,1,1)
        ax1.plot(k_VW, y1W, color='b', label='V(W) Chi2 Sup')
        ax1.plot(k_VW, y2W, '--', color='b',label='V(W) Chi2 Centro' )
        ax1.plot(k_VW, y3W, color='b', label='V(W) Chi2 Inf' )
        ax1.fill_between(k_VW,y1W,y3W, facecolor='blue', alpha=0.5)
        ax1.plot(k_VW,yt1W, color='g', label='V(W) t-Student Sup')
        ax1.plot(k_VW,yt2W, '--', color='g', label='V(W) t-Student Centro')
        ax1.plot(k_VW,yt3W, color='g', label='V(W) t-Student Inf')
        ax1.fill_between(k_VW, yt1W,yt3W, facecolor='yellow', alpha=0.5)
        ax1.hlines(y=v_w_Analit, xmin=k_inicial, xmax=k_VW[-1], color='red', linestyles='dotted', label='V(W) analitico')
        #ax1.legend('Limite Superior Chi2','Centro Chi2')
        ax1.set_title(disciplina+" Rho = "+ str(lamb))
        ax1.set_xlabel('Tamanho da rodada (k)')
        ax1.set_ylabel('unidades de tempo')
        legend = ax1.legend(loc='upper left')
        f1.savefig(saida1 + '.png')
        #plt.subplot(2,1,2)
        f1, ax2 = plt.subplots() 
        ax2.plot(k_VNq,y1Nq, color='c', label='V(Nq) Chi2 Sup')
        ax2.plot(k_VNq,y2Nq, '--', color='c', label='V(Nq) Chi2 Centro')
        ax2.plot(k_VNq,y3Nq, color='c', label='V(Nq) Chi2 Inf')
        ax2.fill_between(k_VNq,y1Nq,y3Nq, facecolor='m', alpha=0.33)
        ax2.plot(k_VNq,yt1Nq, color='g', label='V(Nq) t-Student Sup')
        ax2.plot(k_VNq,yt2Nq, '--', color='g', label='V(Nq) t-Student Centro')
        ax2.plot(k_VNq,y3tNq, color='g', label='V(Nq) t-Student Inf')
        ax2.fill_between(k_VNq, yt1Nq,y3tNq, facecolor='yellow', alpha=0.5)
        ax2.hlines(y=v_Nq_Analit, xmin=k_inicial, xmax=k_VNq[-1], color='red', linestyles='dotted' , label='V(Nq) analitico')
        ax2.set_xlabel('Tamanho da rodada (k)')
        ax2.set_ylabel('Clientes')
    
        legend2 = ax2.legend(loc='upper left')
        #ax.plot(x,y)
        #ax.set(xlabel=x_legenda, ylabel=y_legenda, title=disciplina.upper())
        #ax.set_ylim(0, 1)
        #ax.grid()
                    
        f1.savefig(saida2+ '.png')

            
    print(f'------ Tempo total de simulação: {(datetime.now() - inicioSim)} ------')
    print(f'semente utilizada: {r}; proxima semente: {random.random()}')
