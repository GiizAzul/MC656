from abc import ABC, abstractmethod


class SistemaEleitoral(ABC):
    """Interface base para todos os motores de votação do projeto."""
    
    @abstractmethod
    def apurar_vencedor(self) -> str | None:
        """Executa a lógica matemática da eleição e retorna o vencedor."""

    @abstractmethod
    def iniciar_votacao(self) -> None:
        """Inicia o ciclo de votação."""

    @abstractmethod
    def registrar_voto(self, eleitor_id: str, voto: object) -> None:
        """Registra voto individual."""

    @abstractmethod
    def encerrar_votacao(self) -> None:
        """Encerra o ciclo de votação."""