from .base import Usuario

class EstudanteCACo(Usuario):
    def __init__(self, id, username, senha, nome_real, ra: int):
        super().__init__(id, username, senha, nome_real)
        self.ra = ra

    @property
    def escopo(self) -> str:
        return "CACO_ESTUDANTE"

