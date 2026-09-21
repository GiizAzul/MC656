from enum import Enum

from src.autenticacao.base import Usuario
from src.botc import SistemaEleitoralBotC
from src.cli import io_utils
from src.cli.telas.resultados import exibir_contadores_botc, exibir_resultado_eleicao


class AcaoBotc(Enum):
    """Ações disponíveis na tela do Blood on the Clocktower."""

    REGISTRAR = "1"
    CONTADORES = "2"
    APURAR = "3"
    VOLTAR = "0"


_NOMES_ACAO = {
    AcaoBotc.REGISTRAR: "Registrar votos de um nomeado",
    AcaoBotc.CONTADORES: "Ver contadores",
    AcaoBotc.APURAR: "Apurar execução",
    AcaoBotc.VOLTAR: "Voltar",
}


def acoes_disponiveis(escopo: str) -> list[AcaoBotc]:
    """Retorna as ações visíveis para o escopo do usuário (lógica pura)."""
    acoes = []
    if escopo == "BOTC_STORYTELLER":
        acoes.append(AcaoBotc.REGISTRAR)
    acoes += [AcaoBotc.CONTADORES, AcaoBotc.APURAR, AcaoBotc.VOLTAR]
    return acoes


def decidir_acao(escolha: str, acoes: list[AcaoBotc]) -> AcaoBotc | None:
    """Decide qual ação foi escolhida a partir da entrada do usuário."""
    valores_validos = [acao.value for acao in acoes]
    chave = io_utils.decidir_por_chave(escolha, valores_validos)
    return AcaoBotc(chave) if chave is not None else None


def decidir_num_votos(entrada: str) -> int | None:
    """Converte a entrada em um número de votos válido, ou None se inválida."""
    try:
        return int(entrada.strip())
    except ValueError:
        return None


def tela_botc(sistema: SistemaEleitoralBotC, usuario: Usuario) -> None:
    """Menu de ações do Blood on the Clocktower, respeitando o escopo do usuário."""
    acoes = acoes_disponiveis(usuario.escopo)

    while True:
        io_utils.imprimir_titulo(f"Blood on the Clocktower ({usuario.nome_real})")
        io_utils.imprimir_menu([(acao.value, _NOMES_ACAO[acao]) for acao in acoes])

        escolha = input("Opção: ")
        acao = decidir_acao(escolha, acoes)

        if acao is None:
            io_utils.imprimir_erro("Opção inválida.")
            continue
        if acao == AcaoBotc.VOLTAR:
            return

        _executar_acao(acao, sistema)


def _executar_acao(acao: AcaoBotc, sistema: SistemaEleitoralBotC) -> None:
    """Executa a ação escolhida, tratando as exceções lançadas pelo domínio."""
    if acao == AcaoBotc.REGISTRAR:
        _executar_registro(sistema)
    elif acao == AcaoBotc.CONTADORES:
        exibir_contadores_botc(sistema)
    elif acao == AcaoBotc.APURAR:
        resultado = sistema.apurar_vencedor()
        exibir_resultado_eleicao("Resultado da votação", resultado)


def _executar_registro(sistema: SistemaEleitoralBotC) -> None:
    """Coleta o nome do nomeado e a contagem de votos, e registra no sistema."""
    nomeado = input("Nome do jogador nomeado: ").strip()
    entrada_votos = input("Quantidade de votos recebidos: ")
    num_votos = decidir_num_votos(entrada_votos)

    if num_votos is None:
        io_utils.imprimir_erro("Quantidade de votos inválida.")
        return

    try:
        sistema.registrar_votacao(nomeado, num_votos)
        io_utils.imprimir_sucesso("Votos registrados com sucesso.")
    except ValueError as erro:
        io_utils.imprimir_erro(str(erro))
