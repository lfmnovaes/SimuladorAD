class Evento(object):
    def __init__(self, tempo, refCliente, tipo):
        self.tempo = tempo
        self.refCliente = refCliente
        # tipo de evento {0 = Chegada; 1 = termino servico}
        self.tipo = tipo
