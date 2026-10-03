from abc import ABC, abstractmethod
import uuid


class Usuario(ABC):
    """Classe base abstrata para todos os usuários do sistema."""
    def __init__(self, username:str, senha: str, nome_real: str):
        self.id = uuid.uuid4()
        self.username = username
        self.senha = senha
        self.nome_real = nome_real

    @property
    def id(self) -> str:
        """Garante que o ID seja acessível apenas para leitura (imutável)."""
        return self._id

    @property
    @abstractmethod
    def escopo(self) -> str:
        """Identificar qual o contexto entre as possíveis eleições"""

    def validar_senha(self, tentativa: str) -> bool:
        return self.senha == tentativa

class ServicoAutenticacao:
    """Gerencia o registro e login centralizado de todos os escopos."""
    def __init__(self):
        # O banco agora usa exclusivamente o User_ID como chave primária interna
        self._banco_por_id: dict[str, Usuario] = {}
        # Mapeamento secundário apenas para permitir o login via username
        self._mapa_usernames: dict[str, str] = {}

    def registrar(self, usuario: Usuario) -> None:
        if not usuario.username.strip() or not usuario.senha.strip():
            raise ValueError("Erro: Username e senha não podem ser vazios")
        if usuario.username in self._mapa_usernames:
            raise ValueError(f"Erro: username {usuario.username} já existente.")
        
        self._banco_por_id[usuario.id] = usuario
        self._mapa_usernames[usuario.username] = usuario.id

    def login(self, username: str, senha_tentativa: str) -> Usuario:
        user_id = self._mapa_usernames.get(username)
        if not user_id:
            raise ValueError(f"Erro: Usuário {username} não encontrado.")
        
        usuario = self._banco_por_id.get(user_id)

        if not usuario:
            raise ValueError(f"Erro: Usuário {username} não encontrado.")
        if not usuario.validar_senha(senha_tentativa):
            raise ValueError("Erro: Senha incorreta.")
        
        return usuario