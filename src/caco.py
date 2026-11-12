import math
import time
from enum import Enum

from .interfaces import SistemaEleitoral


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

    def __init__(
        self,
        alunos_cadastrados_ids: list[str],
        eleitores_ids: list[str],
        duracao_ciclo: float,
    ):
        """Inicializa uma eleição da Assembleia do CACo."""
        # Inicia no estado AguardandoVotacao
        super().__init__() 

        alunos = set(alunos_cadastrados_ids)

        # Verifica se há eleitores duplicados.
        if len(eleitores_ids) != len(set(eleitores_ids)):
            raise ValueError(
                "A presença de um participante não pode ser "
                "registrada mais de uma vez."
            )

        # Verifica se todos os eleitores são alunos cadastrados.
        for eleitor_id in eleitores_ids:
            if eleitor_id not in alunos:
                raise ValueError(
                    f"O User_ID '{eleitor_id}' não está cadastrado como aluno."
                )

        # Verifica o quórum mínimo.
        num_alunos = len(alunos)
        quorum = math.ceil(num_alunos / 10)
        num_eleitores = len(eleitores_ids)

        if num_eleitores < quorum:
            raise RuntimeError(
                f"Quórum mínimo não foi satisfeito: "
                f"são necessários pelo menos {quorum} eleitores."
            )

        # Verifica se a duração do ciclo é válida.
        if duracao_ciclo <= 0:
            raise ValueError("A duração do ciclo deve ser maior que zero.")

        self.alunos_cadastrados = alunos
        self.eleitores = set(eleitores_ids)
        self.duracao_ciclo = duracao_ciclo

        # Inicializa o registro de quem já votou.
        self.votantes: set[str] = set()

        # Inicializa os contadores.
        self.contadores: dict[OpcaoVoto, int] = {
            OpcaoVoto.APROVAR: 0,
            OpcaoVoto.REJEITAR: 0,
            OpcaoVoto.ABSTER: 0,
        }

        # Controla a temporização.
        self.inicio_votacao: float | None = None

    def iniciar_votacao(self) -> None:
        """Inicia ciclo de votação."""
        super().iniciar_votacao() # utiliza o metodo iniciar_votacao de SistemaEleitoral
        self.inicio_votacao = time.monotonic() # implementa temporizacao

    def tempo_acabou(self) -> bool:
        """Verifica se o tempo da votação terminou."""

        # se a votação ainda não começou, não acabou
        if self.inicio_votacao is None:
            return False

        tempo_decorrido = time.monotonic() - self.inicio_votacao

        return tempo_decorrido >= self.duracao_ciclo
 
    def registrar_voto(self, eleitor_id:str, opcao: OpcaoVoto) -> None:
        """Registra o voto de um eleitor"""

        # garante voto único
        if eleitor_id in self.votantes:
            raise ValueError("O eleitor já registrou um voto nesta votação.") # value error?

        if eleitor_id not in self.eleitores:
            raise ValueError("Usuário não autorizado a votar nesta assembleia.")

        self.contadores[opcao] += 1
        self.votantes.add(eleitor_id)

    def encerrar_votacao(self) -> None:
        """Encerra ciclo de votação."""
        super().encerrar_votacao()
        self.inicio_votacao = None
                
    def obter_contadores(self) -> dict[str, int]:
        """Retorna a quantidade de votos de cada opção."""
    
        return {
            "APROVAR": self.contadores[OpcaoVoto.APROVAR],
            "REJEITAR": self.contadores[OpcaoVoto.REJEITAR],
            "ABSTER": self.contadores[OpcaoVoto.ABSTER]
        }
    
    def apurar_vencedor(self) -> str | None:
        """Apura o resultado final da votação."""
    
        votos_aprovar = self.contadores[OpcaoVoto.APROVAR]
        votos_rejeitar = self.contadores[OpcaoVoto.REJEITAR]
    
        # abstenções não participam da decisão
        votos_nao_nulos = votos_aprovar + votos_rejeitar
    
        # se ninguém aprovou ou rejeitou, considera-se veto
        if votos_nao_nulos == 0:
            return "VETADA"
    
        # aprovação precisa ser maior que 50%
        if votos_aprovar * 2 > votos_nao_nulos:
            return "APROVADA"
    
        # rejeição e empate
        return "VETADA"