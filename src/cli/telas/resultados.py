import time
from collections.abc import Callable
from typing import Any

from src.caco import EleicaoAssembleia
from src.cli import cli_utils


def exibir_contadores_caco(eleicao: EleicaoAssembleia) -> None:
    """Exibe os contadores atuais (APROVAR/REJEITAR/ABSTER) da votação do CACo."""
    contadores = eleicao.obter_contadores()
    cli_utils.imprimir_titulo("Contadores")
    for opcao, total in contadores.items():
        cli_utils.imprimir_mensagem(f"  {opcao}: {total}")


def exibir_contadores_botc(sistema: Any) -> None:
    """Exibe os contadores atuais de votos registrados no Blood on the Clocktower."""
    cli_utils.imprimir_titulo("Contadores")
    if not sistema.votos:
        cli_utils.imprimir_mensagem("  Nenhum voto registrado ainda.")
        return
    for candidato, votos in sistema.votos.items():
        cli_utils.imprimir_mensagem(f"  {candidato}: {votos}")


def exibir_resultado_eleicao(rotulo: str, resultado: str | None) -> None:
    """Exibe o resultado final de uma apuração de forma padronizada.

    Reutilizada por qualquer contexto (Austrália, BotC, apuração do CACo)
    para tratar de modo uniforme o caso em que ainda não há um vencedor.
    """
    if resultado is None:
        cli_utils.imprimir_mensagem(f"{rotulo}: ainda não há resultado definido.")
    else:
        cli_utils.imprimir_mensagem(f"{rotulo}: {resultado}")


def acompanhar_votacao_caco(
    eleicao: EleicaoAssembleia,
    dormir: Callable[[float], None] = time.sleep,
    intervalo: float = 5.0,
    max_iteracoes: int | None = None,
) -> None:
    """Reimprime os contadores periodicamente até o tempo da votação acabar.

    `dormir` e `max_iteracoes` são injetáveis para permitir testar o loop sem
    depender de tempo real (`time.sleep`) e sem torná-lo infinito nos testes;
    em uso normal, o loop termina sozinho quando `eleicao.tempo_acabou()`
    passa a ser verdadeiro.
    """
    iteracoes = 0
    while not eleicao.tempo_acabou():
        exibir_contadores_caco(eleicao)
        iteracoes += 1
        if max_iteracoes is not None and iteracoes >= max_iteracoes:
            return
        dormir(intervalo)

    exibir_contadores_caco(eleicao)
    cli_utils.imprimir_mensagem("Tempo esgotado.")
