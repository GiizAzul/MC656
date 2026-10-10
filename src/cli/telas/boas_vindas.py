
from enum import Enum

from src.cli import cli_utils


class EscolhaInicial(Enum):
    """Opções do menu inicial, antes de qualquer autenticação."""

    LOGIN = "1"
    CADASTRO = "2"
    SAIR = "0"

def tela_boas_vindas() -> EscolhaInicial:
    """Pergunta se o usuário quer entrar, criar uma conta nova, ou sair.

    Repete a leitura até que uma opção válida seja informada.
    """
    cli_utils.imprimir_titulo("Sistema de votação")
    cli_utils.imprimir_menu([
        (EscolhaInicial.LOGIN.value, "Entrar"),
        (EscolhaInicial.CADASTRO.value, "Criar conta"),
        (EscolhaInicial.SAIR.value, "Sair"),
    ])

    while True:
        escolha = input("Opção: ")
        chave = cli_utils.decidir_por_chave(escolha, [opcao.value for opcao in EscolhaInicial])
        if chave is not None:
            return EscolhaInicial(chave)
        cli_utils.imprimir_erro("Opção inválida.")