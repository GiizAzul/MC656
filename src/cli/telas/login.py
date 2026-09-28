from getpass import getpass

from src.autenticacao.base import ServicoAutenticacao, Usuario
from src.cli import cli_utils


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
    senha = getpass("Senha: ")

    try:
        usuario = servico.login(username, senha)
    except ValueError as erro:
        cli_utils.imprimir_erro(str(erro))
        return None

    cli_utils.imprimir_sucesso(f"Bem-vindo(a), {usuario.nome_real}!")
    return usuario
