from .base import Usuario


class EstudanteCACo(Usuario):
    def __init__(self, id: int, username: str, senha: str, nome_real: str, ra: int):
        super().__init__(id, username, senha, nome_real)
        self.ra = ra

    @property
    def escopo(self) -> str:
        return "CACO_ESTUDANTE"


class GestaoCACo(Usuario):
    """Membro com permissão para criar pautas e chamar uma assembléia"""
    @property
    def escopo(self) -> str:
        return "CACO_GESTAO"