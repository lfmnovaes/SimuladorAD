class Evento(object):
    #evento == 0 indica chegada à fila
    #evento == 1 indica começo de serviço
    #evento == 2 indica término de serviço
    def __init__(self, tipo_de_evento, cliente, tempo, rodada):
        self.tipo_de_evento = tipo_de_evento
        self.tempo_evento = tempo
        self.cliente = cliente
        self.rodada = rodada
