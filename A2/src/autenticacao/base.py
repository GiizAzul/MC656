from abc import ABC, abstractmethod
from typing import Dict

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
        pass

    def validar_senha(self, tentativa: str) -> bool:
        return self.senha == tentativa

class ServicoAutenticacao:
    """Gerencia o registro e login centralizado de todos os escopos."""
    def __init__(self):
        self._banco: Dict[str, Usuario] = {}

    def registrar(self, usuario: Usuario) -> None:
        if usuario.username in self._banco:
            raise ValueError(f"Erro: username {usuario.username} já existente.")
        self._banco[usuario.username] = usuario

    def login(self, username: str, senha_tentativa: str) -> Usuario:
        usuario = self._banco.get(username)
        if not usuario:
            raise ValueError("Erro: Usuário não encontrado.")
        if not usuario.validar_senha(senha_tentativa):
            raise ValueError("Erro: Senha incorreta.")
        return usuario