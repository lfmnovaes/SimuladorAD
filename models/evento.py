class Evento(object):
    def __init__(self, tipo_de_evento, cliente, tempo, rodada):
        #tipo de evento: 0 - chegada à fila / 1 - começo serviço / 2 - término do serviço
        self.tipo_de_evento = tipo_de_evento
        self.tempo_evento = tempo
        self.cliente = cliente
        self.rodada = rodada
