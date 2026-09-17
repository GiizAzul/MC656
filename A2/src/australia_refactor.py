from typing import List, Dict, Optional

class EleicaoAustralia():
    """"Classe para apuração utilizando voto único transferível."""

    def __init__(self, candidatos: List[str], cedulas: List[List[str]]):
        self.candidatos_oficiais = set(candidatos)
        self.candidatos = {nome: True for nome in candidatos}
        self.cedulas = cedulas