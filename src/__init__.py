from src.routers import australia_router, auth_router, botc_router, caco_router

from .australia import EleicaoAustralia
from .botc import JogadorBotC, SistemaEleitoralBotC, StatusJogador
from .caco import EleicaoAssembleia
from .interfaces import SistemaEleitoral

__all__ = [
    "EleicaoAssembleia",
    "EleicaoAustralia",
    "JogadorBotC",
    "SistemaEleitoral",
    "SistemaEleitoralBotC",
    "StatusJogador",
    "australia_router",
    "auth_router",
    "botc_router",
    "caco_router",
]
