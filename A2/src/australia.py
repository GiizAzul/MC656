from typing import List, Dict, Optional
import copy
from src import SistemaEleitoral

class EleicaoAustralia(SistemaEleitoral):
    """"Classe para apuração utilizando voto único transferível."""

    def __init__(self, candidatos: List[str], cedulas: List[List[str]]):
        self.candidatos_oficiais = set(candidatos)
        self.candidatos = {nome: True for nome in candidatos}
        self.cedulas = copy.deepcopy(cedulas)

        # Validação que os dados são íntegros com os candidatos registrados
        num_candidatos = len(candidatos)
        for i, cedula in enumerate(cedulas):
            # Verifica se tem o tamanho exato com todos os candidatos escolhidos
            if len(cedula) != num_candidatos:
                raise ValueError(f"Erro de cédula {i+1} inválida: Você deve ranquear exatamente todos os {num_candidatos} candidatos.")
            
            # Verifica se não está colocando candidato que não existem, anular o voto ou repetindo ele
            if set(cedula) != self.candidatos_oficiais:
                raise ValueError(f"Erro de cédula {i+1} inválida: A cédula contém candidatos duplicados ou não registrados.")
            
            self.cedulas.append(cedula[:])

    def _contar_primeiras_preferencias(self) -> Dict[str, int]:
        """Método privado para contabilizar os votos válidos da rodada atual."""
        contagem = {nome: 0 for nome, ativo in self.candidatos.items() if ativo}
        
        for cedula in self.cedulas:
            # Varre o ranking do eleitor e dá o voto para o primeiro candidato ativo que achar
            for opcao in cedula:
                if self.candidatos.get(opcao):
                    contagem[opcao] += 1
                    break  # Pula para o próximo eleitor
        return contagem

    def apurar_vencedor(self) -> Optional[str]:
        """Executa os turnos de eliminação até encontrar o vencedor."""
        if not self.candidatos or not self.cedulas: # Podia resumir o condicional mas assim fica mais legível
            return None

        while True:
            contagem = self._contar_primeiras_preferencias()
            total_votos_validos = sum(contagem.values())

            if total_votos_validos == 0:
                return None

            # Verifica se alguém atingiu maioria absoluta
            for candidato, votos in contagem.items():
                if votos > total_votos_validos / 2:
                    return candidato

            # Encontra o candidato com menos votos
            candidato_menos_votado = min(contagem, key=contagem.get)
            
            # Elimina o candidato mudando o status para inativo
            self.candidatos[candidato_menos_votado] = False

            # Condição de parada (se sobrou apenas 1 ativo, ele vence)
            ativos = [c for c, ativo in self.candidatos.items() if ativo]
            if len(ativos) == 1:
                return ativos[0]
            elif len(ativos) == 0:
                return None