from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING
"""Evita dependencia circular entre classes"""
if TYPE_CHECKING:
    from .interfaces import SistemaEleitoral

class EstadoVotacao(ABC):
    """Define as transições possíveis em cada estado."""
    
    @property
    def nome(self) -> str:
        """Retorna o nome do estado para exibição."""
        return {
            AguardandoVotacao: "AGUARDANDO",
            EmVotacao: "VOTACAO",
            Encerrada: "ENCERRADA",
        }[type(self)]

    def iniciar_votacao(self) -> "EstadoVotacao":
        raise RuntimeError(
            "A votação já foi iniciada."
        )
    
    def apurar_voto(self, sistema: SistemaEleitoral, eleitor_id: str, voto: object) -> None:
        raise RuntimeError(
            "Não existe um ciclo de votação ativo."
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
    def iniciar_votacao(self) -> EstadoVotacao:
        raise RuntimeError("A votação já foi encerrada.")