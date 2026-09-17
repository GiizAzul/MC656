from .base import Usuario

class JogadorBOTC(Usuario):
    """Participante da roda de votação da cidade."""
    @property
    def escopo(self) -> str:
        return "BOTC_JOGADOR"

class StoryTellerBOTC(Usuario):
    """Coordena o jogo e nesse escopo seta o tempo e o início do dia."""
    @property
    def escopo(self):
        return "BOTC_STORYTELLER"