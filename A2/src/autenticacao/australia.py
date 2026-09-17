from .base import Usuario


class CandidatoAustralia(Usuario):
    """Usuário que pode ser votado nas eleições."""
    @property
    def escopo(self) -> str:
        return "AUSTRALIA_CANDIDATO"
        
class EleitorAustralia(Usuario):
    """Usuário comum, apenas com permissão para votar."""
    @property
    def escopo(self) -> str:
        return "AUSTRALIA_ELEITOR"
