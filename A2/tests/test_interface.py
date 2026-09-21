import pytest

from src.autenticacao import (
    CandidatoAustralia,
    EleitorAustralia,
    EstudanteCACo,
    GestaoCACo,
    JogadorBOTC,
    ServicoAutenticacao,
    StoryTellerBOTC,
)
from src.botc import SistemaEleitoralBotC
from src.caco import EleicaoAssembleia, OpcaoVoto

from src.cli import cli_utils
from src.cli.app import Estado, decidir_proximo_estado, executar_app
from src.cli.sessao import Sessao
from src.cli.telas.australia import (
    AcaoAustralia,
    acoes_disponiveis as acoes_australia,
    cedula_e_valida,
    decidir_acao as decidir_acao_australia,
    montar_ranking,
    tela_australia,
)
from src.cli.telas.boas_vindas import EscolhaInicial, tela_boas_vindas
from src.cli.telas.botc import (
    AcaoBotc,
    acoes_disponiveis as acoes_botc,
    decidir_acao as decidir_acao_botc,
    decidir_num_votos,
    tela_botc,
)
from src.cli.telas.caco import (
    AcaoCaco,
    acoes_disponiveis as acoes_caco,
    decidir_acao as decidir_acao_caco,
    decidir_opcao_voto,
    tela_caco,
)
from src.cli.telas.cadastro import TipoConta, construir_usuario, decidir_tipo, tela_cadastro
from src.cli.telas.login import tela_login
from src.cli.telas.resultados import (
    acompanhar_votacao_caco,
    exibir_contadores_botc,
    exibir_contadores_caco,
    exibir_resultado_eleicao,
)
from src.cli.telas.selecao_contexto import (
    OpcaoContexto,
    decidir_opcao,
    opcoes_disponiveis,
    tela_selecao_contexto,
)


# ---------------------------------------------------------------------------
# Helpers para simular entrada do usuário nas telas interativas.
# ---------------------------------------------------------------------------

def _patch_inputs(monkeypatch: pytest.MonkeyPatch, respostas: list[str]) -> None:
    """Faz `input()` retornar, em sequência, cada item de `respostas`."""
    respostas_iter = iter(respostas)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(respostas_iter))


def _patch_getpass(monkeypatch: pytest.MonkeyPatch, alvo: str, respostas: list[str]) -> None:
    """Faz `getpass()` (importado em `alvo`) retornar, em sequência, cada item de `respostas`."""
    respostas_iter = iter(respostas)
    monkeypatch.setattr(alvo, lambda prompt="": next(respostas_iter))


# ---------------------------------------------------------------------------
# cli_utils.py
# ---------------------------------------------------------------------------

def test_imprimir_titulo(capsys: pytest.CaptureFixture[str]) -> None:
    cli_utils.imprimir_titulo("Meu Título")
    saida = capsys.readouterr().out
    assert "=== Meu Título ===" in saida


def test_imprimir_mensagem(capsys: pytest.CaptureFixture[str]) -> None:
    cli_utils.imprimir_mensagem("Olá mundo")
    assert "Olá mundo" in capsys.readouterr().out


def test_imprimir_erro(capsys: pytest.CaptureFixture[str]) -> None:
    cli_utils.imprimir_erro("Deu ruim")
    assert "[ERRO] Deu ruim" in capsys.readouterr().out


def test_imprimir_sucesso(capsys: pytest.CaptureFixture[str]) -> None:
    cli_utils.imprimir_sucesso("Deu certo")
    assert "[OK] Deu certo" in capsys.readouterr().out


def test_imprimir_menu(capsys: pytest.CaptureFixture[str]) -> None:
    cli_utils.imprimir_menu([("1", "Opção Um"), ("2", "Opção Dois")])
    saida = capsys.readouterr().out
    assert "  [1] Opção Um" in saida
    assert "  [2] Opção Dois" in saida


def test_decidir_por_chave_valida() -> None:
    assert cli_utils.decidir_por_chave("1", ["1", "2", "3"]) == "1"


def test_decidir_por_chave_com_espacos() -> None:
    """A entrada deve ser normalizada (strip) antes de validar."""
    assert cli_utils.decidir_por_chave("  2  ", ["1", "2", "3"]) == "2"


def test_decidir_por_chave_invalida() -> None:
    assert cli_utils.decidir_por_chave("9", ["1", "2", "3"]) is None


def test_decidir_por_chave_vazia() -> None:
    assert cli_utils.decidir_por_chave("", ["1", "2", "3"]) is None


# ---------------------------------------------------------------------------
# sessao.py
# ---------------------------------------------------------------------------

def test_sessao_valores_padrao() -> None:
    sessao = Sessao()
    assert sessao.usuario is None
    assert sessao.eleicao_caco is None
    assert sessao.candidatos_australia == []
    assert sessao.cedulas_australia == []
    assert sessao.sistema_botc is None
    assert sessao.proximo_id_usuario == 100
    assert sessao.esta_logado() is False


def test_sessao_logar_e_deslogar() -> None:
    sessao = Sessao()
    usuario = JogadorBOTC(1, "jogador", "senha", "Jogador Um")

    sessao.logar(usuario)
    assert sessao.esta_logado() is True
    assert sessao.usuario is usuario

    sessao.deslogar()
    assert sessao.esta_logado() is False
    assert sessao.usuario is None


# ---------------------------------------------------------------------------
# telas/boas_vindas.py
# ---------------------------------------------------------------------------

def test_tela_boas_vindas_escolha_valida(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_inputs(monkeypatch, ["1"])
    assert tela_boas_vindas() == EscolhaInicial.LOGIN
    assert "Sistema de votação" in capsys.readouterr().out


@pytest.mark.parametrize(
    "chave, esperado",
    [("1", EscolhaInicial.LOGIN), ("2", EscolhaInicial.CADASTRO), ("0", EscolhaInicial.SAIR)],
)
def test_tela_boas_vindas_todas_opcoes(
    monkeypatch: pytest.MonkeyPatch, chave: str, esperado: EscolhaInicial
) -> None:
    _patch_inputs(monkeypatch, [chave])
    assert tela_boas_vindas() == esperado


def test_tela_boas_vindas_repete_ate_opcao_valida(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_inputs(monkeypatch, ["x", "9", "2"])
    assert tela_boas_vindas() == EscolhaInicial.CADASTRO
    saida = capsys.readouterr().out
    assert saida.count("[ERRO] Opção inválida.") == 2


# ---------------------------------------------------------------------------
# telas/login.py
# ---------------------------------------------------------------------------

@pytest.fixture
def servico_com_jogador() -> ServicoAutenticacao:
    servico = ServicoAutenticacao()
    servico.registrar(JogadorBOTC(1, "joao", "senha123", "João"))
    return servico


def test_tela_login_sucesso(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    servico_com_jogador: ServicoAutenticacao,
) -> None:
    _patch_inputs(monkeypatch, ["joao"])
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["senha123"])

    usuario = tela_login(servico_com_jogador)

    assert usuario is not None
    assert usuario.nome_real == "João"
    assert "Bem-vindo(a), João!" in capsys.readouterr().out


def test_tela_login_senha_incorreta(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    servico_com_jogador: ServicoAutenticacao,
) -> None:
    _patch_inputs(monkeypatch, ["joao"])
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["errada"])

    usuario = tela_login(servico_com_jogador)

    assert usuario is None
    assert "[ERRO]" in capsys.readouterr().out


def test_tela_login_usuario_inexistente(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    servico_com_jogador: ServicoAutenticacao,
) -> None:
    _patch_inputs(monkeypatch, ["fantasma"])
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["123"])

    usuario = tela_login(servico_com_jogador)

    assert usuario is None
    assert "não encontrado" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# telas/cadastro.py
# ---------------------------------------------------------------------------

def test_decidir_tipo_valido() -> None:
    assert decidir_tipo("1") == TipoConta.CACO_ESTUDANTE


def test_decidir_tipo_invalido() -> None:
    assert decidir_tipo("99") is None


@pytest.mark.parametrize(
    "tipo, classe_esperada, escopo_esperado",
    [
        (TipoConta.CACO_GESTAO, GestaoCACo, "CACO_GESTAO"),
        (TipoConta.AUSTRALIA_ELEITOR, EleitorAustralia, "AUSTRALIA_ELEITOR"),
        (TipoConta.AUSTRALIA_CANDIDATO, CandidatoAustralia, "AUSTRALIA_CANDIDATO"),
        (TipoConta.BOTC_JOGADOR, JogadorBOTC, "BOTC_JOGADOR"),
        (TipoConta.BOTC_STORYTELLER, StoryTellerBOTC, "BOTC_STORYTELLER"),
    ],
)
def test_construir_usuario_tipos_sem_ra(
    tipo: TipoConta, classe_esperada: type, escopo_esperado: str
) -> None:
    usuario = construir_usuario(tipo, 1, "user", "senha", "Nome Completo")
    assert isinstance(usuario, classe_esperada)
    assert usuario.escopo == escopo_esperado


def test_construir_usuario_estudante_caco_com_ra() -> None:
    usuario = construir_usuario(TipoConta.CACO_ESTUDANTE, 2, "aluno", "senha", "Aluno", ra=123456)
    assert isinstance(usuario, EstudanteCACo)
    assert usuario.ra == 123456


def test_construir_usuario_estudante_caco_sem_ra_falha() -> None:
    with pytest.raises(ValueError, match="RA é obrigatório"):
        construir_usuario(TipoConta.CACO_ESTUDANTE, 2, "aluno", "senha", "Aluno")


def test_tela_cadastro_tipo_invalido(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    servico = ServicoAutenticacao()
    _patch_inputs(monkeypatch, ["99"])

    resultado = tela_cadastro(servico, 100)

    assert resultado is None
    assert "Tipo de conta inválido." in capsys.readouterr().out


def test_tela_cadastro_fluxo_completo_estudante_com_retries(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exercita os retries: senha vazia, senhas não batem,
    RA não numérico e RA com tamanho errado."""
    servico = ServicoAutenticacao()
    _patch_inputs(
        monkeypatch,
        [
            "1",  # tipo: estudante do CACo
            "novo_user",  # username
            "Fulano de Tal",  # nome_real
            "abc",  # RA inválido (não numérico)
            "12",  # RA inválido (não tem 6 dígitos)
            "123456",  # RA válido
        ],
    )
    _patch_getpass(
        monkeypatch,
        "src.cli.telas.cadastro.getpass",
        ["", "", "abc", "xyz", "123456", "123456"],
        # 1ª tentativa: senha vazia -> repete
        # 2ª tentativa: senhas não batem ("abc" != "xyz") -> repete
        # 3ª tentativa: senhas batem -> segue
    )

    usuario = tela_cadastro(servico, 100)

    saida = capsys.readouterr().out
    assert "A senha não pode ser vazia." in saida
    assert "Senhas não batem." in saida
    assert "RA inválido: deve ser um número." in saida
    assert "RA inválido: deve ter 6 dígitos." in saida
    assert "Conta criada com sucesso! Bem-vindo(a), Fulano de Tal." in saida

    assert usuario is not None
    assert isinstance(usuario, EstudanteCACo)
    assert usuario.ra == 123456
    assert usuario.id == 100
    # o serviço realmente registrou o novo usuário
    assert servico.login("novo_user", "123456").nome_real == "Fulano de Tal"


def test_tela_cadastro_username_duplicado(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    servico = ServicoAutenticacao()
    servico.registrar(GestaoCACo(1, "existente", "senha", "Já Existe"))

    _patch_inputs(monkeypatch, ["2", "existente", "Outra Pessoa"])
    _patch_getpass(monkeypatch, "src.cli.telas.cadastro.getpass", ["senha123", "senha123"])

    resultado = tela_cadastro(servico, 200)

    assert resultado is None
    assert "[ERRO]" in capsys.readouterr().out


def test_tela_cadastro_conta_nao_estudante_nao_pede_ra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contas que não são de estudante do CACo não devem exigir RA
    (não sobra input não consumido)."""
    servico = ServicoAutenticacao()
    _patch_inputs(monkeypatch, ["2", "gestor_novo", "Gestor Novo"])
    _patch_getpass(monkeypatch, "src.cli.telas.cadastro.getpass", ["senha123", "senha123"])

    usuario = tela_cadastro(servico, 300)

    assert isinstance(usuario, GestaoCACo)
    assert not hasattr(usuario, "ra")


# ---------------------------------------------------------------------------
# telas/selecao_contexto.py
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "escopo, esperado",
    [
        ("CACO_ESTUDANTE", [OpcaoContexto.CACO]),
        ("CACO_GESTAO", [OpcaoContexto.CACO]),
        ("AUSTRALIA_ELEITOR", [OpcaoContexto.AUSTRALIA]),
        ("AUSTRALIA_CANDIDATO", [OpcaoContexto.AUSTRALIA]),
        ("BOTC_JOGADOR", [OpcaoContexto.BOTC]),
        ("BOTC_STORYTELLER", [OpcaoContexto.BOTC]),
        ("ESCOPO_DESCONHECIDO", []),
    ],
)
def test_opcoes_disponiveis_por_escopo(escopo: str, esperado: list[OpcaoContexto]) -> None:
    assert opcoes_disponiveis(escopo) == esperado


def test_decidir_opcao_valida() -> None:
    opcoes = [OpcaoContexto.CACO]
    assert decidir_opcao("1", opcoes) == OpcaoContexto.CACO


def test_decidir_opcao_logout_sempre_disponivel() -> None:
    """A opção de logout deve funcionar mesmo não estando na lista de contextos do usuário."""
    opcoes = [OpcaoContexto.CACO]
    assert decidir_opcao("0", opcoes) == OpcaoContexto.LOGOUT


def test_decidir_opcao_invalida() -> None:
    opcoes = [OpcaoContexto.CACO]
    assert decidir_opcao("2", opcoes) is None


def test_tela_selecao_contexto_repete_ate_opcao_valida(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    aluno = EstudanteCACo(1, "aluno", "senha", "Aluno Teste", 123456)
    _patch_inputs(monkeypatch, ["9", "1"])

    resultado = tela_selecao_contexto(aluno)

    assert resultado == OpcaoContexto.CACO
    assert "Opção inválida." in capsys.readouterr().out


def test_tela_selecao_contexto_logout(monkeypatch: pytest.MonkeyPatch) -> None:
    eleitor = EleitorAustralia(1, "eleitor", "senha", "Eleitor Teste")
    _patch_inputs(monkeypatch, ["0"])

    assert tela_selecao_contexto(eleitor) == OpcaoContexto.LOGOUT


# ---------------------------------------------------------------------------
# telas/caco.py
# ---------------------------------------------------------------------------

def test_acoes_disponiveis_caco_estudante() -> None:
    acoes = acoes_caco("CACO_ESTUDANTE")
    assert AcaoCaco.INICIAR not in acoes
    assert AcaoCaco.ENCERRAR not in acoes
    assert acoes == [AcaoCaco.VOTAR, AcaoCaco.CONTADORES, AcaoCaco.APURAR, AcaoCaco.VOLTAR]


def test_acoes_disponiveis_caco_gestao() -> None:
    acoes = acoes_caco("CACO_GESTAO")
    assert acoes == [
        AcaoCaco.VOTAR,
        AcaoCaco.CONTADORES,
        AcaoCaco.INICIAR,
        AcaoCaco.ENCERRAR,
        AcaoCaco.APURAR,
        AcaoCaco.VOLTAR,
    ]


def test_decidir_acao_caco_valida_e_invalida() -> None:
    acoes = [AcaoCaco.VOTAR, AcaoCaco.VOLTAR]
    assert decidir_acao_caco("1", acoes) == AcaoCaco.VOTAR
    assert decidir_acao_caco("5", acoes) is None


@pytest.mark.parametrize(
    "escolha, esperado",
    [("1", OpcaoVoto.APROVAR), ("2", OpcaoVoto.REJEITAR), ("3", OpcaoVoto.ABSTER), ("9", None)],
)
def test_decidir_opcao_voto(escolha: str, esperado: OpcaoVoto | None) -> None:
    assert decidir_opcao_voto(escolha) == esperado


@pytest.fixture
def eleicao_caco() -> EleicaoAssembleia:
    alunos = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    eleitores = ["a", "b", "c"]
    return EleicaoAssembleia(alunos, eleitores, duracao_ciclo=60.0)


def test_tela_caco_fluxo_completo_gestao(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    eleicao_caco: EleicaoAssembleia,
) -> None:
    gestor = GestaoCACo(1, "gestor", "senha", "Gestor Um")
    _patch_inputs(
        monkeypatch,
        [
            "9",  # ação inválida
            "3",  # iniciar votação
            "1",  # votar
            "1",  # aprovar
            "2",  # ver contadores
            "5",  # apurar
            "4",  # encerrar votação
            "0",  # voltar
        ],
    )

    tela_caco(eleicao_caco, gestor)

    saida = capsys.readouterr().out
    assert "Opção inválida." in saida
    assert "Votação iniciada." in saida
    assert "Voto registrado com sucesso." in saida
    assert "APROVAR: 1" in saida
    assert "Resultado da votação: APROVADA" in saida
    assert "Votação encerrada." in saida


def test_tela_caco_votar_opcao_invalida(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    eleicao_caco: EleicaoAssembleia,
) -> None:
    aluno = EstudanteCACo(1, "a", "senha", "Aluno A", 111111)
    eleicao_caco.iniciar_votacao()
    _patch_inputs(monkeypatch, ["1", "9", "0"])  # votar -> opção de voto inválida -> voltar

    tela_caco(eleicao_caco, aluno)

    assert "Opção de voto inválida." in capsys.readouterr().out


def test_tela_caco_iniciar_duas_vezes_mostra_erro(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    eleicao_caco: EleicaoAssembleia,
) -> None:
    gestor = GestaoCACo(1, "gestor", "senha", "Gestor Um")
    eleicao_caco.iniciar_votacao()  # já iniciada por fora
    _patch_inputs(monkeypatch, ["3", "0"])  # tenta iniciar de novo -> voltar

    tela_caco(eleicao_caco, gestor)

    assert "A votação já está em andamento." in capsys.readouterr().out


def test_tela_caco_estudante_nao_ve_opcoes_de_gestao(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    eleicao_caco: EleicaoAssembleia,
) -> None:
    """Como INICIAR não está nas ações do estudante,
    escolher "3" deve ser tratado como inválido."""
    aluno = EstudanteCACo(1, "a", "senha", "Aluno A", 111111)
    _patch_inputs(monkeypatch, ["3", "0"])

    tela_caco(eleicao_caco, aluno)

    assert "Opção inválida." in capsys.readouterr().out
    assert eleicao_caco.estado.value == "AGUARDANDO"


# ---------------------------------------------------------------------------
# telas/australia.py
# ---------------------------------------------------------------------------

def test_acoes_disponiveis_australia() -> None:
    assert acoes_australia() == [
        AcaoAustralia.VOTAR,
        AcaoAustralia.CANDIDATOS,
        AcaoAustralia.APURAR,
        AcaoAustralia.VOLTAR,
    ]


def test_decidir_acao_australia() -> None:
    acoes = acoes_australia()
    assert decidir_acao_australia("1", acoes) == AcaoAustralia.VOTAR
    assert decidir_acao_australia("9", acoes) is None


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Ana,Beto,Caio", ["Ana", "Beto", "Caio"]),
        ("Ana, Beto , Caio", ["Ana", "Beto", "Caio"]),  # espaços extras são removidos
        ("Ana,,Beto", ["Ana", "Beto"]),  # entradas vazias são descartadas
        ("", []),
    ],
)
def test_montar_ranking(entrada: str, esperado: list[str]) -> None:
    assert montar_ranking(entrada) == esperado


def test_cedula_e_valida_com_todos_candidatos() -> None:
    candidatos = ["Ana", "Beto", "Caio"]
    assert cedula_e_valida(["Beto", "Ana", "Caio"], candidatos) is True


def test_cedula_e_valida_tamanho_errado() -> None:
    assert cedula_e_valida(["Ana", "Beto"], ["Ana", "Beto", "Caio"]) is False


def test_cedula_e_valida_candidato_repetido_ou_invalido() -> None:
    candidatos = ["Ana", "Beto", "Caio"]
    assert cedula_e_valida(["Ana", "Ana", "Caio"], candidatos) is False
    assert cedula_e_valida(["Ana", "Beto", "Ninguem"], candidatos) is False


def test_tela_australia_fluxo_completo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    candidatos = ["Ana", "Beto", "Caio"]
    cedulas: list[list[str]] = []
    usuario = EleitorAustralia(1, "eleitor", "senha", "Eleitor Um")

    _patch_inputs(
        monkeypatch,
        [
            "9",  # ação inválida
            "2",  # ver candidatos
            "1",  # votar
            "Ana,Beto",  # cédula inválida (faltando Caio)
            "1",  # votar de novo
            "Ana,Beto,Caio",  # cédula válida
            "3",  # apurar
            "0",  # voltar
        ],
    )

    tela_australia(candidatos, cedulas, usuario)

    saida = capsys.readouterr().out
    assert "Opção inválida." in saida
    assert "Candidatos: Ana, Beto, Caio" in saida
    assert "Você deve ranquear exatamente todos os candidatos" in saida
    assert "Voto registrado com sucesso." in saida
    assert len(cedulas) == 1
    assert cedulas[0] == ["Ana", "Beto", "Caio"]
    assert "Vencedor da Eleição Austrália: Ana" in saida


def test_tela_australia_apurar_com_cedulas_invalidas_mostra_erro(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Se a lista de cédulas acumulada não bater com os candidatos, `EleicaoAustralia`
    lança `ValueError` na apuração e a tela deve tratá-lo mostrando uma mensagem de erro."""
    candidatos = ["Ana", "Beto", "Caio"]
    cedulas_invalidas = [["Ana", "Ninguem", "Caio"]]
    usuario = EleitorAustralia(1, "eleitor", "senha", "Eleitor Um")

    _patch_inputs(monkeypatch, ["3", "0"])  # apurar -> voltar

    tela_australia(candidatos, cedulas_invalidas, usuario)

    assert "[ERRO]" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# telas/botc.py
# ---------------------------------------------------------------------------

def test_acoes_disponiveis_botc_storyteller() -> None:
    assert acoes_botc("BOTC_STORYTELLER") == [
        AcaoBotc.REGISTRAR,
        AcaoBotc.CONTADORES,
        AcaoBotc.APURAR,
        AcaoBotc.VOLTAR,
    ]


def test_acoes_disponiveis_botc_jogador_sem_registrar() -> None:
    assert acoes_botc("BOTC_JOGADOR") == [AcaoBotc.CONTADORES, AcaoBotc.APURAR, AcaoBotc.VOLTAR]


def test_decidir_acao_botc() -> None:
    acoes = acoes_botc("BOTC_STORYTELLER")
    assert decidir_acao_botc("1", acoes) == AcaoBotc.REGISTRAR
    assert decidir_acao_botc("9", acoes) is None


@pytest.mark.parametrize(
    "entrada, esperado",
    [("5", 5), (" 3 ", 3), ("0", 0), ("abc", None), ("", None)],
)
def test_decidir_num_votos(entrada: str, esperado: int | None) -> None:
    assert decidir_num_votos(entrada) == esperado


def test_tela_botc_fluxo_completo_storyteller(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    sistema = SistemaEleitoralBotC(jogadores_vivos=5)
    narrador = StoryTellerBOTC(1, "narrador", "senha", "Narrador")

    _patch_inputs(
        monkeypatch,
        [
            "9",  # ação inválida
            "1",  # registrar
            "Fulano",  # nomeado
            "abc",  # quantidade inválida
            "1",  # registrar de novo
            "Fulano",
            "3",  # 3 votos (maioria de 5 jogadores = 2.5)
            "2",  # ver contadores
            "3",  # apurar
            "0",  # voltar
        ],
    )

    tela_botc(sistema, narrador)

    saida = capsys.readouterr().out
    assert "Opção inválida." in saida
    assert "Quantidade de votos inválida." in saida
    assert "Votos registrados com sucesso." in saida
    assert "Fulano: 3" in saida
    assert "Resultado da votação: Fulano" in saida


def test_tela_botc_registrar_votos_alem_do_limite_mostra_erro(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    sistema = SistemaEleitoralBotC(jogadores_vivos=5)
    narrador = StoryTellerBOTC(1, "narrador", "senha", "Narrador")

    _patch_inputs(monkeypatch, ["1", "Fulano", "10", "0"])  # 10 > 5 jogadores vivos

    tela_botc(sistema, narrador)

    assert "[ERRO]" in capsys.readouterr().out


def test_tela_botc_jogador_nao_pode_registrar(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Como REGISTRAR não está entre as ações de um jogador comum, a chave "1" deve
    ser tratada como opção inválida (o menu nem oferece essa ação para esse escopo)."""
    sistema = SistemaEleitoralBotC(jogadores_vivos=5)
    jogador = JogadorBOTC(2, "jogador", "senha", "Jogador Um")

    _patch_inputs(monkeypatch, ["1", "0"])

    tela_botc(sistema, jogador)

    assert "Opção inválida." in capsys.readouterr().out
    assert sistema.votos == {}


# ---------------------------------------------------------------------------
# telas/resultados.py
# ---------------------------------------------------------------------------

def test_exibir_contadores_caco(capsys: pytest.CaptureFixture[str]) -> None:
    eleicao = EleicaoAssembleia(["a", "b"], ["a"], duracao_ciclo=10.0)
    eleicao.iniciar_votacao()
    eleicao.registrar_voto("a", OpcaoVoto.APROVAR)

    exibir_contadores_caco(eleicao)

    saida = capsys.readouterr().out
    assert "APROVAR: 1" in saida
    assert "REJEITAR: 0" in saida
    assert "ABSTER: 0" in saida


def test_exibir_contadores_botc_sem_votos(capsys: pytest.CaptureFixture[str]) -> None:
    sistema = SistemaEleitoralBotC(jogadores_vivos=3)
    exibir_contadores_botc(sistema)
    assert "Nenhum voto registrado ainda." in capsys.readouterr().out


def test_exibir_contadores_botc_com_votos(capsys: pytest.CaptureFixture[str]) -> None:
    sistema = SistemaEleitoralBotC(jogadores_vivos=3)
    sistema.registrar_votacao("Fulano", 2)
    exibir_contadores_botc(sistema)
    assert "Fulano: 2" in capsys.readouterr().out


def test_exibir_resultado_eleicao_sem_resultado(capsys: pytest.CaptureFixture[str]) -> None:
    exibir_resultado_eleicao("Vencedor", None)
    assert "ainda não há resultado definido" in capsys.readouterr().out


def test_exibir_resultado_eleicao_com_resultado(capsys: pytest.CaptureFixture[str]) -> None:
    exibir_resultado_eleicao("Vencedor", "Fulano")
    assert "Vencedor: Fulano" in capsys.readouterr().out


def test_acompanhar_votacao_caco_para_com_max_iteracoes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Com `max_iteracoes`, o loop deve parar antes do tempo acabar, sem imprimir
    a mensagem de "Tempo esgotado.", e chamar `dormir` uma vez a menos que o
    número de vezes que os contadores foram exibidos."""
    eleicao = EleicaoAssembleia(["a", "b"], ["a"], duracao_ciclo=1000.0)
    eleicao.iniciar_votacao()

    chamadas_dormir: list[float] = []
    acompanhar_votacao_caco(
        eleicao, dormir=chamadas_dormir.append, intervalo=2.0, max_iteracoes=3
    )

    saida = capsys.readouterr().out
    assert saida.count("=== Contadores ===") == 3
    assert len(chamadas_dormir) == 2
    assert chamadas_dormir == [2.0, 2.0]
    assert "Tempo esgotado." not in saida


def test_acompanhar_votacao_caco_para_quando_tempo_acaba(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Sem o tempo restante, o loop deve encerrar sozinho e imprimir "Tempo esgotado."."""
    eleicao = EleicaoAssembleia(["a", "b"], ["a"], duracao_ciclo=0.0001)
    eleicao.iniciar_votacao()

    acompanhar_votacao_caco(eleicao, dormir=lambda intervalo: None, intervalo=0.0)

    assert "Tempo esgotado." in capsys.readouterr().out


# ---------------------------------------------------------------------------
# app.py
# ---------------------------------------------------------------------------

def test_estados_da_aplicacao_existem() -> None:
    nomes = {estado.name for estado in Estado}
    assert nomes == {
        "BOAS_VINDAS",
        "LOGIN",
        "CADASTRO",
        "SELECAO_CONTEXTO",
        "VOTACAO_CACO",
        "VOTACAO_AUSTRALIA",
        "VOTACAO_BOTC",
        "SAIR",
    }


@pytest.mark.parametrize(
    "opcao, estado_esperado",
    [
        (OpcaoContexto.CACO, Estado.VOTACAO_CACO),
        (OpcaoContexto.AUSTRALIA, Estado.VOTACAO_AUSTRALIA),
        (OpcaoContexto.BOTC, Estado.VOTACAO_BOTC),
        (OpcaoContexto.LOGOUT, Estado.BOAS_VINDAS),
    ],
)
def test_decidir_proximo_estado(
    opcao: OpcaoContexto, estado_esperado: Estado
) -> None:
    assert decidir_proximo_estado(opcao) == estado_esperado


def test_executar_app_sair_direto(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_inputs(monkeypatch, ["0"])  # boas-vindas -> sair

    executar_app(ServicoAutenticacao(), Sessao())

    assert "Até logo!" in capsys.readouterr().out


def test_executar_app_login_falha_sem_tentar_novamente(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    servico = ServicoAutenticacao()
    servico.registrar(GestaoCACo(1, "g", "s", "Gestor"))

    _patch_inputs(monkeypatch, ["1", "g", "n"])  # login -> usuário -> "tentar de novo? n"
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["senhaerrada"])

    executar_app(servico, Sessao())

    saida = capsys.readouterr().out
    assert "Erro: Senha incorreta." in saida
    assert "Até logo!" in saida


def test_executar_app_login_falha_e_tenta_novamente(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    servico = ServicoAutenticacao()
    servico.registrar(GestaoCACo(1, "g", "s", "Gestor"))

    # login -> usuário -> "tentar de novo? s" -> volta pra boas-vindas -> sair
    _patch_inputs(monkeypatch, ["1", "g", "s", "0"])
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["senhaerrada"])

    executar_app(servico, Sessao())

    saida = capsys.readouterr().out
    # a tela de boas-vindas deve ter sido mostrada de novo após o retry
    assert saida.count("=== Sistema de votação ===") == 2
    assert "Até logo!" in saida


def test_executar_app_cadastro_falha_volta_para_boas_vindas(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # cadastro -> tipo inválido -> boas-vindas -> sair
    _patch_inputs(monkeypatch, ["2", "99", "0"])

    executar_app(ServicoAutenticacao(), Sessao())

    saida = capsys.readouterr().out
    assert "Tipo de conta inválido." in saida
    assert "Até logo!" in saida


def test_executar_app_fluxo_completo_caco(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Login com sucesso -> vota na Assembleia do CACo -> apura -> logout -> sai."""
    servico = ServicoAutenticacao()
    servico.registrar(GestaoCACo(1, "gestor", "senha123", "Gestor Geral"))

    eleicao_caco = EleicaoAssembleia(
        ["gestor", "a", "b", "c", "d", "e", "f", "g", "h", "i"], ["gestor"], duracao_ciclo=100.0
    )
    sessao = Sessao(eleicao_caco=eleicao_caco)

    _patch_inputs(
        monkeypatch,
        [
            "1",
            "gestor",  # login
            "1",  # selecao_contexto -> CACO
            "3",  # iniciar votação
            "1",
            "1",  # votar -> aprovar
            "5",  # apurar
            "0",  # voltar pra selecao_contexto
            "0",  # logout
            "0",  # sair
        ],
    )
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["senha123"])

    executar_app(servico, sessao)

    saida = capsys.readouterr().out
    assert "Bem-vindo(a), Gestor Geral!" in saida
    assert "Assembleia do CACo (Gestor Geral)" in saida
    assert "Resultado da votação: APROVADA" in saida
    assert "Até logo!" in saida


def test_executar_app_fluxo_completo_australia(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    servico = ServicoAutenticacao()
    servico.registrar(EleitorAustralia(1, "eleitor", "senha123", "Eleitor Um"))
    sessao = Sessao(candidatos_australia=["Ana", "Beto"])

    _patch_inputs(
        monkeypatch,
        [
            "1",
            "eleitor",  # login
            "2",  # selecao_contexto -> AUSTRALIA
            "2",  # ver candidatos
            "0",  # voltar
            "0",  # logout
            "0",  # sair
        ],
    )
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["senha123"])

    executar_app(servico, sessao)

    saida = capsys.readouterr().out
    assert "Eleição Austrália (Eleitor Um)" in saida
    assert "Candidatos: Ana, Beto" in saida
    assert "Até logo!" in saida


def test_executar_app_fluxo_completo_botc(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cobre a integração do contexto Blood on the Clocktower no loop principal:
    `Estado.VOTACAO_BOTC` precisa ser tratado em `executar_app` para que o usuário
    consiga efetivamente chegar em `tela_botc` (ver Estado no app.py)."""
    servico = ServicoAutenticacao()
    servico.registrar(StoryTellerBOTC(1, "narrador", "senha123", "Narrador"))
    sessao = Sessao(sistema_botc=SistemaEleitoralBotC(jogadores_vivos=5))

    _patch_inputs(
        monkeypatch,
        [
            "1",
            "narrador",  # login
            "3",  # selecao_contexto -> BOTC
            "2",  # ver contadores
            "0",  # voltar
            "0",  # logout
            "0",  # sair
        ],
    )
    _patch_getpass(monkeypatch, "src.cli.telas.login.getpass", ["senha123"])

    executar_app(servico, sessao)

    saida = capsys.readouterr().out
    assert "Blood on the Clocktower (Narrador)" in saida
    assert "Nenhum voto registrado ainda." in saida
    assert "Até logo!" in saida


def test_executar_app_fluxo_completo_cadastro_ate_selecao_de_contexto(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cria uma conta nova (jogador do BotC) e confirma que ela já entra logada
    e vê o contexto correspondente ao escopo criado."""
    servico = ServicoAutenticacao()
    sessao = Sessao()

    _patch_inputs(
        monkeypatch,
        [
            "2",  # boas-vindas -> cadastro
            "5",  # tipo: jogador do BotC
            "novato",  # username
            "Novato",  # nome_real
            "0",  # selecao_contexto -> logout
            "0",  # sair
        ],
    )
    _patch_getpass(monkeypatch, "src.cli.telas.cadastro.getpass", ["senha123", "senha123"])

    executar_app(servico, sessao)

    saida = capsys.readouterr().out
    assert "Conta criada com sucesso! Bem-vindo(a), Novato." in saida
    assert "Selecione o contexto (Novato)" in saida
    assert "Blood on the Clocktower" in saida
    assert "Até logo!" in saida
    # a conta deve ter ficado persistida no serviço de autenticação
    assert servico.login("novato", "senha123").nome_real == "Novato"