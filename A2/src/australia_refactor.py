from typing import List, Dict, Optional

class EleicaoAustralia():
    """"Classe para apuração utilizando voto único transferível."""

    def __init__(self, candidatos: List[str], cedulas: List[List[str]]):
        self.candidatos_oficiais = set(candidatos)
        self.candidatos = {nome: True for nome in candidatos}
        self.cedulas = [cedula[:] for cedula in cedulas if cedula]  # Cópia para não alterar o original do frontend

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