import pytest

from src.autenticacao import (
    CandidatoAustralia,
    EstudanteCACo,
    GestaoCACo,
    JogadorBOTC,
    ServicoAutenticacao,
)


@pytest.fixture
def auth():
    """Fixture do pytest para criar um serviço limpo antes de cada teste."""
    return ServicoAutenticacao()

def testa_login_varios_escopos(auth: ServicoAutenticacao) -> None:
    """Cria usuários de todos os escopos e testa eles todos"""

    aluno = EstudanteCACo(0, "Gabriel Soares", "Gabriel Soares", "Gabriel Soares", 3)
    jogador = JogadorBOTC(1, "Leo_bct", "EuSouOLeo", "Leonardo Carvalho De Luca")
    candidato = CandidatoAustralia(2, "Samuel_aus", "Sans_Undertale", "Samuel")
    # O mesmo serviço registra todos eles
    auth.registrar(aluno)
    auth.registrar(jogador)
    auth.registrar(candidato)

    # Verifica se os escopos são mantidos no login
    logado_aluno = auth.login("Gabriel Soares", "Gabriel Soares")
    assert logado_aluno.escopo == "CACO_ESTUDANTE"
    assert hasattr(logado_aluno, "ra")

    logado_jogador = auth.login("Leo_bct", "EuSouOLeo")
    assert logado_jogador.escopo == "BOTC_JOGADOR"

def testa_bloqueia_username_duplicado(auth: ServicoAutenticacao) -> None:
    """Um usuário não pode ter o mesmo login mesmo em escopos diferentes"""
    auth.registrar(EstudanteCACo(0 , "samuel", "123", "Samuel", 5))

    with pytest.raises(ValueError, match="já existe"):
        auth.registrar(JogadorBOTC(0, "samuel", "213", "Samuel Impostor"))

def testa_falha_de_seguranca(auth: ServicoAutenticacao) -> None:
    auth.registrar(JogadorBOTC(5, "Tekpix", "senhasegura", "Yago"))

    with pytest.raises(ValueError, match="Senha incorreta"):
        auth.login("Tekpix", "senhainsegura")

    with pytest.raises(ValueError, match="Usuário fantasma não encontrado"):
        auth.login("fantasma", "123")

def testa_input_vazio(auth: ServicoAutenticacao) -> None:
    """Verifica se a trava de segurança contra strings vazias está funcionando"""
    usuario_invalido = JogadorBOTC(10, "", "    ", "Ninguém")

    with pytest.raises(ValueError, match="não podem ser vazios"):
        auth.registrar(usuario_invalido)

