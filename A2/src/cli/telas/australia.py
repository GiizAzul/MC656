from enum import Enum

from src.australia import EleicaoAustralia
from src.autenticacao.base import Usuario
from src.cli import cli_utils
from src.cli.telas.resultados import exibir_resultado_eleicao


class AcaoAustralia(Enum):
    """Ações disponíveis na tela da Eleição Austrália."""

    VOTAR = "1"
    CANDIDATOS = "2"
    APURAR = "3"
    VOLTAR = "0"


_NOMES_ACAO = {
    AcaoAustralia.VOTAR: "Votar (ranquear candidatos)",
    AcaoAustralia.CANDIDATOS: "Ver candidatos",
    AcaoAustralia.APURAR: "Apurar vencedor",
    AcaoAustralia.VOLTAR: "Voltar",
}


def acoes_disponiveis() -> list[AcaoAustralia]:
    """Retorna as ações disponíveis nesta tela.

    Diferente do CACo e do BotC, a Eleição Austrália não distingue
    permissões de gestão neste fluxo: qualquer usuário autenticado no
    contexto pode votar, consultar os candidatos ou apurar o resultado.
    """
    return [
        AcaoAustralia.VOTAR,
        AcaoAustralia.CANDIDATOS,
        AcaoAustralia.APURAR,
        AcaoAustralia.VOLTAR,
    ]


def decidir_acao(escolha: str, acoes: list[AcaoAustralia]) -> AcaoAustralia | None:
    """Decide qual ação foi escolhida a partir da entrada do usuário."""
    valores_validos = [acao.value for acao in acoes]
    chave = cli_utils.decidir_por_chave(escolha, valores_validos)
    return AcaoAustralia(chave) if chave is not None else None


def montar_ranking(entrada: str) -> list[str]:
    """Converte uma entrada separada por vírgulas em uma lista ordenada de candidatos."""
    return [item.strip() for item in entrada.split(",") if item.strip()]


def cedula_e_valida(ranking: list[str], candidatos: list[str]) -> bool:
    """Verifica se o ranking contém exatamente todos os candidatos, sem repetição."""
    return len(ranking) == len(candidatos) and set(ranking) == set(candidatos)


def tela_australia(candidatos: list[str], cedulas: list[list[str]], usuario: Usuario) -> None:
    """Menu de ações da Eleição Austrália."""
    acoes = acoes_disponiveis()

    while True:
        cli_utils.imprimir_titulo(f"Eleição Austrália ({usuario.nome_real})")
        cli_utils.imprimir_menu([(acao.value, _NOMES_ACAO[acao]) for acao in acoes])

        escolha = input("Opção: ")
        acao = decidir_acao(escolha, acoes)

        if acao is None:
            cli_utils.imprimir_erro("Opção inválida.")
            continue
        if acao == AcaoAustralia.VOLTAR:
            return

        _executar_acao(acao, candidatos, cedulas)


def _executar_acao(acao: AcaoAustralia, candidatos: list[str], cedulas: list[list[str]]) -> None:
    """Executa a ação escolhida, tratando as exceções lançadas pelo domínio."""
    if acao == AcaoAustralia.VOTAR:
        _executar_voto(candidatos, cedulas)
    elif acao == AcaoAustralia.CANDIDATOS:
        cli_utils.imprimir_mensagem("Candidatos: " + ", ".join(candidatos))
    elif acao == AcaoAustralia.APURAR:
        try:
            eleicao = EleicaoAustralia(candidatos, cedulas)
        except ValueError as erro:
            cli_utils.imprimir_erro(str(erro))
            return
        resultado = eleicao.apurar_vencedor()
        exibir_resultado_eleicao("Vencedor da Eleição Austrália", resultado)


def _executar_voto(candidatos: list[str], cedulas: list[list[str]]) -> None:
    """Coleta o ranking do eleitor e acumula a cédula na lista compartilhada."""
    cli_utils.imprimir_mensagem(f"Candidatos disponíveis: {', '.join(candidatos)}")
    entrada = input("Digite sua ordem de preferência separada por vírgulas: ")
    ranking = montar_ranking(entrada)

    if not cedula_e_valida(ranking, candidatos):
        cli_utils.imprimir_erro(
            "Você deve ranquear exatamente todos os candidatos, sem repetição."
        )
        return

    cedulas.append(ranking)
    cli_utils.imprimir_sucesso("Voto registrado com sucesso.")
