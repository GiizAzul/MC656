from typing import List
from src import SistemaEleitoral
import math 

class EleicaoAssembleia(SistemaEleitoral):
    """"Classe para apuração utilizando modelo baseado nas assembleias do CACo."""

    def __init__(self, alunos_cadastrados: List[str], eleitores: List[str], duracao_ciclo: float): #talvez checar duplicatas

        # verifica quorum mínimo
        num_alunos = len(alunos_cadastrados)
        quorum = math.ceil(num_alunos/10)
        num_eleitores = len(eleitores)

        if num_eleitores < quorum:
            raise ValueError(f"Quórum mínimo não foi satisfeito: "f"são necessários pelo menos {quorum:.0f} eleitores.")
        
         # Verifica se todos os eleitores são alunos cadastrados
        alunos = set(alunos_cadastrados)

        for eleitor in eleitores:
            if eleitor not in alunos:
                raise ValueError(
                    f"O eleitor '{eleitor}' não está cadastrado como aluno.")

        if duracao_ciclo <= 0:
            raise ValueError("A duração do ciclo deve ser maior que zero.")

        self.alunos_cadastrados = alunos
        self.eleitores = set(eleitores)
        self.duracao_ciclo = duracao_ciclo