import pytest 
from src.autenticacao import ServicoAutenticacao, CandidatoAustralia

@pytest.fixture
def auth():
    return ServicoAutenticacao()

