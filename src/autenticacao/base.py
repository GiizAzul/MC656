import uuid
from abc import ABC, abstractmethod


class Usuario(ABC):
    """Classe base abstrata para todos os usuários do sistema."""
    def __init__(self, username:str, senha: str, nome_real: str):
        self._id = str(uuid.uuid4())
        self.username = username
        self.senha = senha
        self.nome_real = nome_real
        self._escopos_extras: set[str] = set()

    @property
    def id(self) -> str:
        """Garante que o ID seja acessível apenas para leitura (imutável)."""
        return self._id

    @property
    @abstractmethod
    def escopo(self) -> str:
        """Identificar qual o contexto entre as possíveis eleições"""

    def _getattribute_(self, name: str):
        val = super()._getattribute_(name)
        if name == "escopo":
            extras = super()._getattribute_("_escopos_extras")
            if extras:
                return ",".join(sorted({val} | extras))
        return val

    def adicionar_escopo(self, novo_escopo: str, ra: int | None = None) -> None:
        self._escopos_extras.add(novo_escopo)
        if ra is not None:
            self.ra = ra

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
            existente = self._banco_por_id[self._mapa_usernames[usuario.username]]
            if existente.validar_senha(usuario.senha) and usuario.escopo not in existente.escopo:
                ra_novo = getattr(usuario, "ra", None)
                if ra_novo and str(ra_novo) in self._mapa_usernames:
                    raise ValueError(f"Erro: RA {ra_novo} já existente.")
                existente.adicionar_escopo(usuario.escopo, ra=ra_novo)
                if ra_novo:
                    self._mapa_usernames[str(ra_novo)] = existente.id
                return
            raise ValueError(f"Erro: username {usuario.username} já existente.")
        if hasattr(usuario, 'ra') and usuario.ra and str(usuario.ra) in self._mapa_usernames:
            raise ValueError(f"Erro: RA {usuario.ra} já existente.")
        
        self._banco_por_id[usuario.id] = usuario
        self._mapa_usernames[usuario.username] = usuario.id

        if hasattr(usuario, 'ra') and usuario.ra:
            self._mapa_usernames[str(usuario.ra)] = usuario.id  # Permite login via RA

    def login(self, identifier: str, senha_tentativa: str) -> Usuario:
        user_id = self._mapa_usernames.get(identifier)  # Pode ser username ou RA
        if not user_id:
            raise ValueError(f"Erro: Usuário {identifier} não encontrado.")
        
        usuario = self._banco_por_id.get(user_id)

        if not usuario:
            raise ValueError(f"Erro: Usuário {identifier} não encontrado.")
        if not usuario.validar_senha(senha_tentativa):
            raise ValueError("Erro: Senha incorreta.")
        
        return usuario