from enum import Enum

from src.caco import EleicaoAssembleia, OpcaoVoto
from src.autenticacao.base import Usuario
from src.cli import cli_utils


def tela_caco(eleicao: EleicaoAssembleia, usuario: Usuario) -> None:
    while True:
        break