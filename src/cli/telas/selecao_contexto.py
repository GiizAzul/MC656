from enum import Enum

from src.autenticacao.base import Usuario
from src.cli import cli_utils


class OpcaoContexto(Enum):
    """Contextos de votação que podem ser selecionados, e a opção de logout."""

    CACO = "1"
    AUSTRALIA = "2"
    BOTC = "3"
    LOGOUT = "0"


_NOMES_CONTEXTO = {
    OpcaoContexto.CACO: "Assembleia do CACo",
    OpcaoContexto.AUSTRALIA: "Eleição Austrália",
    OpcaoContexto.BOTC: "Blood on the Clocktower",
}

# Escopos de usuário (Usuario.escopo) que têm acesso a cada contexto.
_OPCOES_POR_ESCOPO: dict[str, list[OpcaoContexto]] = {
    "CACO_ESTUDANTE": [OpcaoContexto.CACO],
    "CACO_GESTAO": [OpcaoContexto.CACO],
    "AUSTRALIA_ELEITOR": [OpcaoContexto.AUSTRALIA],
    "AUSTRALIA_CANDIDATO": [OpcaoContexto.AUSTRALIA],
    "BOTC_JOGADOR": [OpcaoContexto.BOTC],
    "BOTC_STORYTELLER": [OpcaoContexto.BOTC],
}


def opcoes_disponiveis(escopo: str) -> list[OpcaoContexto]:
    """Retorna os contextos visíveis para o escopo informado (lógica pura)."""
    return list(_OPCOES_POR_ESCOPO.get(escopo, []))


def decidir_opcao(escolha: str, opcoes: list[OpcaoContexto]) -> OpcaoContexto | None:
    """Decide qual contexto foi escolhido a partir da entrada do usuário."""
    valores_validos = [opcao.value for opcao in opcoes] + [OpcaoContexto.LOGOUT.value]
    chave = cli_utils.decidir_por_chave(escolha, valores_validos)
    if chave is None:
        return None
    return OpcaoContexto(chave)


def tela_selecao_contexto(usuario: Usuario) -> OpcaoContexto:
    """Mostra os contextos disponíveis para o usuário e lê a escolha."""
    opcoes = opcoes_disponiveis(usuario.escopo)

    cli_utils.imprimir_titulo(f"Selecione o contexto ({usuario.nome_real})")
    cli_utils.imprimir_menu([(opcao.value, _NOMES_CONTEXTO[opcao]) for opcao in opcoes])
    cli_utils.imprimir_menu([(OpcaoContexto.LOGOUT.value, "Sair / logout")])

    while True:
        escolha = input("Opção: ")
        resultado = decidir_opcao(escolha, opcoes)
        if resultado is not None:
            return resultado
        cli_utils.imprimir_erro("Opção inválida.")
