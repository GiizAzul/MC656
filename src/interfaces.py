from abc import ABC, abstractmethod
from .estados import AguardandoVotacao, EstadoVotacao

class SistemaEleitoral(ABC):
    """Interface e contexto State dos motores eleitorais."""

    def __init__(self) -> None:
        self.estado: EstadoVotacao = AguardandoVotacao()

    def iniciar_votacao(self) -> None:
        """Inicia a votação por meio do estado atual."""
        self.estado = self.estado.iniciar_votacao()

    def apurar_voto(self, eleitor_id: str, voto: object) -> None:
        """Verifica permissao de votacao"""
        self.estado.apurar_voto(self, eleitor_id, voto)

    def encerrar_votacao(self) -> None:
        """Encerra a votação por meio do estado atual."""
        self.estado = self.estado.encerrar_votacao()

    @abstractmethod
    def apurar_vencedor(self) -> str | None:
        """Executa a lógica matemática da eleição e retorna o vencedor."""

    @abstractmethod
    def registrar_voto(self, eleitor_id: str, voto: object) -> None:
        """Registra voto individual."""