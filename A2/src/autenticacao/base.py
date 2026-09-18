from abc import ABC, abstractmethod


class Usuario(ABC):
    """Classe base abstrata para todos os usuários do sistema."""
    def __init__(self, id: int, username:str, senha: str, nome_real: str):
        self.id = id
        self.username = username
        self.senha = senha
        self.nome_real = nome_real

    @property
    @abstractmethod
    def escopo(self) -> str:
        """Identificar qual o contexto entre as possíveis eleições"""

    def validar_senha(self, tentativa: str) -> bool:
        return self.senha == tentativa

class ServicoAutenticacao:
    """Gerencia o registro e login centralizado de todos os escopos."""
    def __init__(self):
        # self._banco: Dict[str, Usuario] = {}
        self._banco: dict[str, Usuario] = {}

    def registrar(self, usuario: Usuario) -> None:
        if not usuario.username.strip() or not usuario.senha.strip():
            raise ValueError("Erro: Username e senha não podem ser vazios")
        if usuario.username in self._banco:
            raise ValueError(f"Erro: username {usuario.username} já existente.")
        self._banco[usuario.username] = usuario

    def login(self, username: str, senha_tentativa: str) -> Usuario:
        usuario = self._banco.get(username)
        if not usuario:
            raise ValueError(f"Erro: Usuário {username} não encontrado.")
        if not usuario.validar_senha(senha_tentativa):
            raise ValueError("Erro: Senha incorreta.")
        return usuario