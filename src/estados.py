from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING
"""Evita dependencia circular entre classes"""
if TYPE_CHECKING:
    from .interfaces import SistemaEleitoral

class EstadoVotacao(ABC):
    """Define as transições possíveis em cada estado."""

    def iniciar_votacao(self) -> "EstadoVotacao":
        raise RuntimeError(
            "Não é possível iniciar a votação neste estado."
        )
    
    def apurar_voto(self, sistema: SistemaEleitoral, eleitor_id: str, voto: object) -> None:
        raise RuntimeError(
            "Não é possível votar neste estado."
        )

    def encerrar_votacao(self) -> "EstadoVotacao":
        raise RuntimeError(
            "Não é possível encerrar a votação neste estado."
        )


class AguardandoVotacao(EstadoVotacao):
    """Estado anterior ao início da votação."""

    def iniciar_votacao(self) -> EstadoVotacao:
        return EmVotacao()


class EmVotacao(EstadoVotacao):
    """Estado em que os votos podem ser registrados."""

    def apurar_voto(self, sistema: SistemaEleitoral, eleitor_id: str, voto: object) -> None:
        sistema.registrar_voto(eleitor_id, voto)

    def encerrar_votacao(self) -> EstadoVotacao:
        return Encerrada()


class Encerrada(EstadoVotacao):
    """Estado de votação finalizada."""