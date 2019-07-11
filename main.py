#!/usr/bin/env python3

import random
import math
import sys
import argparse
import datetime

from controllers.agendador import *
from controllers.calculadora import *
from models.servidor import *
from models.evento import *
from models.cliente import *

RODADAS = 3200
UTLIZACOES = [0.2, 0.4, 0.6, 0.8, 0.9]
#self, tx_chegada: float, tx_servico: float, k: int, n: int, tipo_fila: int, IC: float, precisao: float, utilizacao: float):
#filaFCFS = Fila(0.2, 1, 100, 3200, 0, 0.95, 0.05, 0.2)

disciplina = 'fcfs'

parser = argparse.ArgumentParser(description='Simulação FCFS/LCFS')
parser.add_argument('disciplina', help='disciplina de atendimento (padrão FCFS)')
args = parser.parse_args()

if (args.disciplina.lower() == "lcfs"):
    print(f'Iniciando com disciplina LCFS')
    disciplina = 'lcfs'
else:
    print(f'Iniciando com disciplina FCFS')
    disciplina = 'fcfs'

class Simulacao(object):
    def __init__(self):
        self.__transiente = True
        #self.tx_chegada = lamb

        print(f'{disciplina}')
        print(f'{RODADAS}')

    def executarFCFS(self):
        print(f'Executando com disciplina FCFS')

    def executarLCFS(self):
        print(f'Executando com disciplina LCFS')


if __name__ == '__main__':

    s = Simulacao()
    if (disciplina == "lcfs"):
        s.executarLCFS()
    else:
        s.executarFCFS()
