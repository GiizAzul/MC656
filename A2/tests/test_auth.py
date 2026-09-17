import pytest 
from src.autenticacao import (
    ServicoAutenticacao, 
    CandidatoAustralia,
    EstudanteCACo,
    GestaoCACo,
    JogadorBOTC)

@pytest.fixture
def auth():
    return ServicoAutenticacao()

def testa_login_varios_escopos(auth: ServicoAutenticacao):
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
    assert logado_aluno.escopo == "CACO_GESTAO"
    assert hasattr(logado_aluno, "ra")

    logado_jogador = auth.login("Leo_bct", "EuSouOLeo")
    assert logado_jogador.escopo == "BOTC_JOGADOR"