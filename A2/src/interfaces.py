from abc import ABC, abstractmethod


class SistemaEleitoral(ABC):
    """Interface base para todos os motores de votação do projeto."""
    
    @abstractmethod
    def apurar_vencedor(self) -> str | None:
        """Executa a lógica matemática da eleição e retorna o vencedor."""
