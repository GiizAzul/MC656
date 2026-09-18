from typing import List, Dict, Set, Optional
from src import SistemaEleitoral
from enum import Enum
import math 
import time

# tipos válidos de voto
class OpcaoVoto(Enum):
    APROVAR = "APROVAR"
    REJEITAR = "REJEITAR"
    ABSTER = "ABSTER"

class Estado(Enum):
    AGUARDANDO = "AGUARDANDO"
    VOTACAO = "VOTACAO"
    ENCERRADA = "ENCERRADA"

class EleicaoAssembleia(SistemaEleitoral):
    """"Classe para apuração utilizando modelo baseado nas assembleias do CACo."""

    def __init__(self, alunos_cadastrados: List[str], eleitores: List[str], duracao_ciclo: float): #talvez checar duplicatas

        # verifica quorum mínimo
        num_alunos = len(alunos_cadastrados)
        quorum = math.ceil(num_alunos/10)
        num_eleitores = len(eleitores)

        if num_eleitores < quorum:
            raise RuntimeError(f"Quórum mínimo não foi satisfeito: "f"são necessários pelo menos {quorum:.0f} eleitores.") # runtime ou value?
        
        # verifica se todos os eleitores são alunos cadastrados
        alunos = set(alunos_cadastrados)

        for eleitor in eleitores:
            if eleitor not in alunos:
                raise ValueError(f"O eleitor '{eleitor}' não está cadastrado como aluno.")

        if duracao_ciclo <= 0:
            raise ValueError("A duração do ciclo deve ser maior que zero.")

        self.alunos_cadastrados = alunos
        self.eleitores = set(eleitores)
        self.duracao_ciclo = duracao_ciclo

        # inicializa registro de quem já votou
        self.votantes: Set[str] = set()

        # inicializa contadores
        self.contadores: Dict[OpcaoVoto, int] = {
                OpcaoVoto.APROVAR: 0,
                OpcaoVoto.REJEITAR: 0,
                OpcaoVoto.ABSTER: 0
        }
        
        # controle de estados e temporização
        self.estado = Estado.AGUARDANDO
        self.inicio_votacao = Optional[float] = None

    def iniciar_votacao(self) -> None:
        """Inicia ciclo de votação."""
    
        # não permite iniciar uma votação já encerrada
        if self.estado == Estado.ENCERRADA:
            raise RuntimeError("A votação já foi encerrada.")
    
        # não permite iniciar uma votação duas vezes
        if self.estado == Estado.VOTACAO:
            raise RuntimeError("A votação já está em andamento.")
    
        self.estado = Estado.VOTACAO
        self.inicio_votacao = time.monotonic()

    def tempo_acabou(self) -> bool:
        """Verifica se o tempo da votação terminou."""

        # se a votação ainda não começou, não acabou
        if self.inicio_votacao is None:
            return False

        tempo_decorrido = time.monotonic() - self.inicio_votacao

        return tempo_decorrido >= self.duracao_ciclo
 
    def registrar_voto (self, eleitor:str, opcao: OpcaoVoto) -> None:
        """Registra o voto de um eleitor"""

        # verifica se está em estado de votação
        if self.estado != Estado.VOTACAO:
            raise RuntimeError("Não existe um ciclo de votação ativo.")

        # garante voto único
        if eleitor in self.votantes:
            raise ValueError("O eleitor já registrou um voto nesta votação.") # value error?

        self.contadores[opcao] += 1
        self.votantes.add(eleitor)

    def encerrar_votacao(self) -> None:
        """Encerra ciclo de votação."""
        
        # Só encerra se ainda estiver acontecendo
        if self.estado == Estado.ENCERRADA:
            return
    
        self.estado = Estado.ENCERRADA
        self.inicio_votacao = None
                
    """Implementar apuracao de vencedor"""