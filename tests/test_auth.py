import uuid

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

    aluno = EstudanteCACo("Gabriel Soares", "Gabriel Soares", "Gabriel Soares", 3)
    jogador = JogadorBOTC("Leo_bct", "EuSouOLeo", "Leonardo Carvalho De Luca")
    candidato = CandidatoAustralia("Samuel_aus", "Sans_Undertale", "Samuel")
    # O mesmo serviço registra todos eles
    auth.registrar(aluno)
    auth.registrar(jogador)
    auth.registrar(candidato)

    # Verifica se os escopos são mantidos no login
    logado_aluno = auth.login("Gabriel Soares", "Gabriel Soares")
    assert logado_aluno.escopo == "CACO_ESTUDANTE"
    assert hasattr(logado_aluno, "ra")
    assert logado_aluno.id == aluno.id 

    logado_jogador = auth.login("Leo_bct", "EuSouOLeo")
    assert logado_jogador.escopo == "BOTC_JOGADOR"

def testa_bloqueia_username_duplicado(auth: ServicoAutenticacao) -> None:
    """Um usuário não pode ter o mesmo login mesmo em escopos diferentes"""
    auth.registrar(EstudanteCACo("samuel", "123", "Samuel", 5))

    with pytest.raises(ValueError, match="já existente"):
        auth.registrar(JogadorBOTC("samuel", "213", "Samuel Impostor"))

def testa_falha_de_seguranca(auth: ServicoAutenticacao) -> None:
    auth.registrar(JogadorBOTC("Tekpix", "senhasegura", "Yago"))

    with pytest.raises(ValueError, match="Senha incorreta"):
        auth.login("Tekpix", "senhainsegura")

    with pytest.raises(ValueError, match="não encontrado"):
        auth.login("fantasma", "123")

def testa_input_vazio(auth: ServicoAutenticacao) -> None:
    """Verifica se a trava de segurança contra strings vazias está funcionando"""
    usuario_invalido = JogadorBOTC("", "    ", "Ninguém")

    with pytest.raises(ValueError, match="não podem ser vazios"):
        auth.registrar(usuario_invalido)

def testa_persistencia_banco(auth: ServicoAutenticacao) -> None:
    """Simula o fluxo: 
    Adm cria conta
    Adm loga
    Banco continua acessível para novos registros
    """
    admin = GestaoCACo("Jucaco", "LeninRules", "Juca")
    auth.registrar(admin)

    # Valida o login do admin
    usuario_ativo = auth.login("Jucaco", "LeninRules")
    assert usuario_ativo.escopo == "CACO_GESTAO"

    # O banco deve continuar operante para novos registros na mesma instância
    aluno = EstudanteCACo("caio_iris", "sla", "Caio", 8)
    auth.registrar(aluno)

    assert auth.login("caio_iris", "sla").nome_real == "Caio"

def testa_id_gerado_e_imutavel(auth: ServicoAutenticacao) -> None:
    """Verifica se o UUID gerado atende os critérios de sistema e segurança."""
    jogador = JogadorBOTC("Giiz", "senhaaaaa", "Giovana")
    
    #Verifica se o ID foi gerado automaticamente como string
    assert jogador.id is not None
    assert isinstance(jogador.id, str)
    
    #Garante que o formato é estritamente um UUID versão 4
    try:
        id_valido = uuid.UUID(jogador.id, version=4)
        assert str(id_valido) == jogador.id
    except ValueError:
        pytest.fail("O identificador gerado não é um UUID v4 válido")
        
    #Garante que a propriedade é read-only
    with pytest.raises(AttributeError):
        jogador.id = "tentando_hackear_e_mudar_o_id"

def testa_banco_corrompido_ou_usuario_deletado(auth: ServicoAutenticacao) -> None:
    """
    Testa a validação de segurança quando um username existe no mapa,
    mas o objeto do usuário não se encontra mais no banco por ID.
    """
    jogador = JogadorBOTC("n sei", "senha123", "Deletado")
    auth.registrar(jogador)
    
    # Simulamos uma inconsistência no banco principal enquanto o mapa de usernames continua apontando para o ID deletado
    del auth._banco_por_id[jogador.id]
    
    with pytest.raises(ValueError, match="não encontrado"):
        auth.login("n sei", "senha123")