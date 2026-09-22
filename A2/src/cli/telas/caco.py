from enum import Enum

from src.autenticacao.base import Usuario
from src.caco import EleicaoAssembleia, OpcaoVoto
from src.cli import cli_utils
from src.cli.telas.resultados import exibir_contadores_caco


class AcaoCaco(Enum):
    """Ações disponíveis na tela da Assembleia do CACo."""

    VOTAR = "1"
    CONTADORES = "2"
    INICIAR = "3"
    ENCERRAR = "4"
    APURAR = "5"
    VOLTAR = "0"


_NOMES_ACAO = {
    AcaoCaco.VOTAR: "Votar",
    AcaoCaco.CONTADORES: "Ver contadores",
    AcaoCaco.INICIAR: "Iniciar votação",
    AcaoCaco.ENCERRAR: "Encerrar votação",
    AcaoCaco.APURAR: "Apurar resultado",
    AcaoCaco.VOLTAR: "Voltar",
}

_MAPA_OPCAO_VOTO = {
    "1": OpcaoVoto.APROVAR,
    "2": OpcaoVoto.REJEITAR,
    "3": OpcaoVoto.ABSTER,
}


def acoes_disponiveis(escopo: str) -> list[AcaoCaco]:
    """Retorna as ações visíveis para o escopo do usuário (lógica pura)."""
    acoes = [AcaoCaco.VOTAR, AcaoCaco.CONTADORES]
    if escopo == "CACO_GESTAO":
        acoes += [AcaoCaco.INICIAR, AcaoCaco.ENCERRAR]
    acoes += [AcaoCaco.APURAR, AcaoCaco.VOLTAR]
    return acoes


def decidir_acao(escolha: str, acoes: list[AcaoCaco]) -> AcaoCaco | None:
    """Decide qual ação foi escolhida a partir da entrada do usuário."""
    valores_validos = [acao.value for acao in acoes]
    chave = cli_utils.decidir_por_chave(escolha, valores_validos)
    return AcaoCaco(chave) if chave is not None else None


def decidir_opcao_voto(escolha: str) -> OpcaoVoto | None:
    """Traduz a entrada do usuário para uma `OpcaoVoto` válida, ou None."""
    chave = cli_utils.decidir_por_chave(escolha, list(_MAPA_OPCAO_VOTO.keys()))
    return _MAPA_OPCAO_VOTO[chave] if chave is not None else None


def tela_caco(eleicao: EleicaoAssembleia, usuario: Usuario) -> None:
    """Menu de ações da Assembleia do CACo, respeitando o escopo do usuário."""
    acoes = acoes_disponiveis(usuario.escopo)

    while True:
        cli_utils.imprimir_titulo(f"Assembleia do CACo ({usuario.nome_real})")
        cli_utils.imprimir_menu([(acao.value, _NOMES_ACAO[acao]) for acao in acoes])

        escolha = input("Opção: ")
        acao = decidir_acao(escolha, acoes)

        if acao is None:
            cli_utils.imprimir_erro("Opção inválida.")
            continue
        if acao == AcaoCaco.VOLTAR:
            return

        _executar_acao(acao, eleicao, usuario)


def _executar_acao(acao: AcaoCaco, eleicao: EleicaoAssembleia, usuario: Usuario) -> None:
    """Executa a ação escolhida, tratando as exceções lançadas pelo domínio."""
    if acao == AcaoCaco.VOTAR:
        _executar_voto(eleicao, usuario)
    elif acao == AcaoCaco.CONTADORES:
        exibir_contadores_caco(eleicao)
    elif acao == AcaoCaco.INICIAR:
        try:
            eleicao.iniciar_votacao()
            cli_utils.imprimir_sucesso("Votação iniciada.")
        except RuntimeError as erro:
            cli_utils.imprimir_erro(str(erro))
    elif acao == AcaoCaco.ENCERRAR:
        eleicao.encerrar_votacao()
        cli_utils.imprimir_sucesso("Votação encerrada.")
    elif acao == AcaoCaco.APURAR:
        resultado = eleicao.apurar_vencedor()
        cli_utils.imprimir_mensagem(f"Resultado da votação: {resultado}")


def _executar_voto(eleicao: EleicaoAssembleia, usuario: Usuario) -> None:
    """Coleta a opção de voto e registra o voto do usuário logado."""
    cli_utils.imprimir_menu([
        ("1", "Aprovar"),
        ("2", "Rejeitar"),
        ("3", "Abster-se"),
    ])
    escolha = input("Seu voto: ")
    opcao = decidir_opcao_voto(escolha)

    if opcao is None:
        cli_utils.imprimir_erro("Opção de voto inválida.")
        return

    try:
        eleicao.registrar_voto(usuario.username, opcao)
        cli_utils.imprimir_sucesso("Voto registrado com sucesso.")
    except (ValueError, RuntimeError) as erro:
        cli_utils.imprimir_erro(str(erro))
