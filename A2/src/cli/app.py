from enum import Enum, auto

from src.autenticacao.base import ServicoAutenticacao
from src.cli.sessao import Sessao
from src.cli.telas.cadastro import tela_cadastro
from src.cli.telas.boas_vindas import EscolhaInicial, tela_boas_vindas
from src.cli.telas.login import tela_login
from src.cli.telas.selecao_contexto import OpcaoContexto, tela_selecao_contexto
from src.cli.telas.caco import tela_caco
from src.cli.telas.australia import tela_australia


class Estado(Enum):
    """Estados possíveis do loop principal da aplicação."""

    BOAS_VINDAS = auto()
    LOGIN = auto()
    CADASTRO = auto()
    SELECAO_CONTEXTO = auto()
    VOTACAO_CACO = auto()
    VOTACAO_AUSTRALIA = auto()
    VOTACAO_BOTC = auto()
    SAIR = auto()


# Mapeia a opção de contexto escolhida na tela de seleção para o próximo estado do loop principal.
_MAPA_CONTEXTO_ESTADO = {
    OpcaoContexto.CACO: Estado.VOTACAO_CACO,
    OpcaoContexto.AUSTRALIA: Estado.VOTACAO_AUSTRALIA,
    OpcaoContexto.BOTC: Estado.VOTACAO_BOTC,
    OpcaoContexto.LOGOUT: Estado.BOAS_VINDAS,
}


def decidir_proximo_estado(opcao: OpcaoContexto) -> Estado:
    """Traduz a opção de contexto escolhida no próximo estado do loop."""
    return _MAPA_CONTEXTO_ESTADO[opcao]


def executar_app(servico_auth: ServicoAutenticacao, sessao: Sessao | None = None) -> None:
    """Executa o loop principal da aplicação de terminal."""
    if sessao is None:
        sessao = Sessao()

    estado = Estado.BOAS_VINDAS

    while estado != Estado.SAIR:
        if estado == Estado.BOAS_VINDAS:
            escolha = tela_boas_vindas()
            if escolha == EscolhaInicial.LOGIN:
                estado = Estado.LOGIN
            elif escolha == EscolhaInicial.CADASTRO:
                estado = Estado.CADASTRO
            else:
                estado = Estado.SAIR

        elif estado == Estado.LOGIN:
            usuario = tela_login(servico_auth)
            if usuario is None:
                resposta = input("Tentar novamente? (s/n): ").strip().lower()
                estado = Estado.BOAS_VINDAS if resposta == "s" else Estado.SAIR
                continue
            sessao.logar(usuario)
            estado = Estado.SELECAO_CONTEXTO

        elif estado == Estado.CADASTRO:
            usuario = tela_cadastro(servico_auth, sessao.proximo_id_usuario)
            if usuario is None:
                estado = Estado.BOAS_VINDAS
                continue
            sessao.proximo_id_usuario += 1
            sessao.logar(usuario)
            estado = Estado.SELECAO_CONTEXTO

        elif estado == Estado.SELECAO_CONTEXTO:
            opcao = tela_selecao_contexto(sessao.usuario)
            if opcao == OpcaoContexto.LOGOUT:
                sessao.deslogar()
            estado = decidir_proximo_estado(opcao)

        elif estado == Estado.VOTACAO_CACO:
            tela_caco(sessao.eleicao_caco, sessao.usuario)
            estado = Estado.SELECAO_CONTEXTO

        elif estado == Estado.VOTACAO_AUSTRALIA:
            tela_australia(sessao.candidatos_australia, sessao.cedulas_australia, sessao.usuario)
            estado = Estado.SELECAO_CONTEXTO

    print("\nAté logo!")
