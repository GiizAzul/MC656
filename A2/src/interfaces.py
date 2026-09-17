from abc import ABC, abstractmethod
from typing import Optional

class SistemaEleitoral(ABC):
    """Interface base para todos os motores de votação do projeto."""
    
    @abstractmethod
    def apurar_vencedor(self) -> Optional[str]:
        """Executa a lógica matemática da eleição e retorna o vencedor."""
        pass