from enum import Enum

from src.autenticacao.base import ServicoAutenticacao, Usuario
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


def tela_login(servico: ServicoAutenticacao) -> Usuario | None:
    """Pede usuário e senha, tenta autenticar e retorna o usuário logado.

    O `ServicoAutenticacao` é recebido como dependência explícita (nunca
    acessado como estado global). Captura o `ValueError` lançado por
    `servico.login(...)` em caso de credenciais inválidas e mostra uma
    mensagem amigável. Retorna o `Usuario` logado, ou `None` se a
    autenticação falhar.
    """
    cli_utils.imprimir_titulo("Login")
    username = input("Usuário: ")
    senha = input("Senha: ")

    try:
        usuario = servico.login(username, senha)
    except ValueError as erro:
        cli_utils.imprimir_erro(str(erro))
        return None

    cli_utils.imprimir_sucesso(f"Bem-vindo(a), {usuario.nome_real}!")
    return usuario
