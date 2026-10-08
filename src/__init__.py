from src.routers import australia_router, auth_router, botc_router, caco_router

from .australia import EleicaoAustralia
from .botc import SistemaEleitoralBotC
from .caco import EleicaoAssembleia
from .interfaces import SistemaEleitoral

__all__ = [
    "EleicaoAssembleia",
    "EleicaoAustralia",
    "SistemaEleitoral",
    "SistemaEleitoralBotC",
    "australia_router",
    "auth_router",
    "botc_router",
    "caco_router"
]
