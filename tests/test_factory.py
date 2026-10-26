import pytest

from src.autenticacao.australia import CandidatoAustralia, EleitorAustralia
from src.autenticacao.botc import JogadorBOTC, StoryTellerBOTC
from src.autenticacao.caco import EstudanteCACo, GestaoCACo
from src.autenticacao.factory import UsuarioFactory


def test_criar_estudante_caco_com_ra_valido():
    usuario = UsuarioFactory.criar(
        tipo_conta="CACO_ESTUDANTE", 
        username="giovana", 
        senha="password123", 
        nome_real="Giovana", 
        ra="123456"
    )
    assert isinstance(usuario, EstudanteCACo)
    assert usuario.username == "giovana"

def test_criar_estudante_caco_sem_ra_levanta_erro():
    with pytest.raises(ValueError, match="RA inválido. Tente novamente."):
        UsuarioFactory.criar(
            tipo_conta="CACO_ESTUDANTE", 
            username="giovana", 
            senha="password123", 
            nome_real="Giovana", 
            ra=None
        )

def test_criar_estudante_caco_com_ra_nao_numerico_levanta_erro():
    with pytest.raises(ValueError, match="RA inválido. Tente novamente."):
        UsuarioFactory.criar(
            tipo_conta="CACO_ESTUDANTE", 
            username="giovana", 
            senha="password123", 
            nome_real="Giovana", 
            ra="abc321"
        )

@pytest.mark.parametrize("tipo_conta, classe_esperada", [
    ("CACO_GESTAO", GestaoCACo),
    ("AUSTRALIA_ELEITOR", EleitorAustralia),
    ("AUSTRALIA_CANDIDATO", CandidatoAustralia),
    ("BOTC_JOGADOR", JogadorBOTC),
    ("BOTC_STORYTELLER", StoryTellerBOTC),
])
def test_criar_demais_tipos_de_conta_sucesso(tipo_conta, classe_esperada):
    usuario = UsuarioFactory.criar(
        tipo_conta=tipo_conta, 
        username="teste_user", 
        senha="password123", 
        nome_real="Usuário Teste"
    )
    assert isinstance(usuario, classe_esperada)
    assert usuario.username == "teste_user"

def test_criar_tipo_conta_desconhecido_levanta_erro():
    with pytest.raises(ValueError, match="Tipo de conta desconhecido."):
        UsuarioFactory.criar(
            tipo_conta="TIPO_INEXISTENTE", 
            username="teste_user", 
            senha="password123", 
            nome_real="Usuário Teste"
        )