import pytest

from src.autenticacao.botc import JogadorBOTC
from src.autenticacao.caco import EstudanteCACo
from src.autenticacao.australia import EleitorAustralia
from src.autenticacao.autorizacao import ControleDeAcesso, ErroAcessoNaoAutorizado


@pytest.fixture
def controle():
    """Fixture que retorna a instância do gerenciador de acesso."""
    return ControleDeAcesso()

@pytest.fixture
def jogador():
    return JogadorBOTC("jogador_botc", "senha123", "João")

@pytest.fixture
def estudante():
    # EstudanteCACo recebe um 4º parâmetro (RA)
    return EstudanteCACo("aluno_caco", "senha123", "Maria", 123456)

@pytest.fixture
def eleitor():
    return EleitorAustralia("eleitor_aus", "senha123", "José")


def testa_extracao_macro_scope(controle: ControleDeAcesso, jogador, estudante, eleitor) -> None:
    """Verifica se os escopos específicos são traduzidos para os MACRO SCOPES corretos."""
    assert controle.extrair_macro_scope(jogador) == "SCOPE_BCT"
    assert controle.extrair_macro_scope(estudante) == "SCOPE_CACO"
    assert controle.extrair_macro_scope(eleitor) == "SCOPE_AUSTRALIA"


def testa_despacho_apos_login(controle: ControleDeAcesso, jogador, estudante, eleitor) -> None:
    """Critério 2: Verifica se o login direciona para o painel nativo correto."""
    assert controle.despachar_apos_login(jogador) == "painel_jogador_bct"
    assert controle.despachar_apos_login(estudante) == "painel_estudante_caco"
    assert controle.despachar_apos_login(eleitor) == "painel_eleitor_australia"


def testa_acesso_recurso_autorizado(controle: ControleDeAcesso, jogador, estudante) -> None:
    """Verifica se usuários conseguem acessar os recursos do próprio escopo."""
    resposta_botc = controle.acessar_recurso(jogador, "painel_jogador_bct")
    assert "Acesso concedido" in resposta_botc

    resposta_caco = controle.acessar_recurso(estudante, "painel_estudante_caco")
    assert "Acesso concedido" in resposta_caco


def testa_acesso_recurso_nao_autorizado(controle: ControleDeAcesso, estudante) -> None:
    """
    Critério 3: Verifica se acessar recurso fora do escopo levanta ErroAcessoNaoAutorizado 
    contendo o HTTP 403 e a rota de fallback.
    """
    # Um estudante tenta acessar o painel de BOTC
    with pytest.raises(ErroAcessoNaoAutorizado) as excinfo:
        controle.acessar_recurso(estudante, "painel_jogador_bct")

    # Verifica se a mensagem possui a punição correta
    assert "HTTP 403" in str(excinfo.value)
    
    # Verifica se o sistema informou para onde o estudante deve ser mandado de volta
    assert excinfo.value.painel_redirecionamento == "painel_estudante_caco"


def testa_acesso_recurso_nao_protegido(controle: ControleDeAcesso, eleitor) -> None:
    """Garante que recursos não listados fiquem abertos por padrão."""
    resposta = controle.acessar_recurso(eleitor, "pagina_inicial_publica")
    assert "Acesso liberado" in resposta