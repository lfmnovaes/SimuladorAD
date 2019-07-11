class Cliente(object):
    def __init__(self, instanteEntrada, Id):
        self.chegada = instanteEntrada
        self.id = Id
        self.tempoServico = -1
        self.tempoFilaEspera = 0.0
        self.tempoSistema = 0.0
