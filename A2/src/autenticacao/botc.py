from .base import Usuario

class JogadorBOTC(Usuario):
    """Participante da roda de votação da cidade."""
    @property
    def escopo(self):
        return "BOTC_JOGADOR"

