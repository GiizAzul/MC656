from enum import Enum

from src.australia import EleicaoAustralia
from src.autenticacao.base import Usuario
from src.cli import cli_utils


def tela_australia(candidatos: list[str], cedulas: list[list[str]], usuario: Usuario) -> None:
    while True:
        break