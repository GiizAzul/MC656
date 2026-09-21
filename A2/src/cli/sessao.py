from dataclasses import dataclass, field

from src.autenticacao.base import Usuario
from src.botc import SistemaEleitoralBotC
from src.caco import EleicaoAssembleia


@dataclass
class Sessao:
    """Mantém o usuário logado e o estado de cada contexto de votação."""

    usuario: Usuario | None = None
    eleicao_caco: EleicaoAssembleia | None = None
    candidatos_australia: list[str] = field(default_factory=list)
    cedulas_australia: list[list[str]] = field(default_factory=list)
    sistema_botc: SistemaEleitoralBotC | None = None
    proximo_id_usuario: int = 100 # usado em telas/cadastro.py ao criar uma nova conta

    def esta_logado(self) -> bool:
        """Indica se há um usuário autenticado na sessão."""
        return self.usuario is not None

    def logar(self, usuario: Usuario) -> None:
        """Registra o usuário autenticado na sessão."""
        self.usuario = usuario

    def deslogar(self) -> None:
        """Remove o usuário autenticado, encerrando a sessão do usuário."""
        self.usuario = None
