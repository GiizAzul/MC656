


class Usuario():
    """Classe base abstrata para todos os usuários do sistema."""

    def __init__(self, id: int, username:str, senha: str, nome_real: str):
        self.id = id
        self.username = username
        self.senha = senha
        self.nome_real = nome_real

    