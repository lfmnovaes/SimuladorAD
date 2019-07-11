class Cliente(object):
    def __init__(self, rodada):
        self.tempo_chegada = 0.0
        self.tempo_comeco_servico = 0.0
        self.tempo_termino_servico = 0.0
        self.rodada_fregues = rodada

    def tempoEmEspera(self):
        return self.tempo_comeco_servico - self.tempo_chegada

    def tempoEmServico(self):
        return self.tempo_termino_servico - self.tempo_comeco_servico

    def tempoTotal(self):
        return self.tempo_termino_servico - self.tempo_chegada
