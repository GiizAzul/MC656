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
        pass

    def validar_senha(self, tentativa: str) -> bool:
        return self.senha == tentativa