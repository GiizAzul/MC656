import uuid

import pytest

from src.autenticacao import (
    CandidatoAustralia,
    EstudanteCACo,
    GestaoAustralia,
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
    gestor_aus = GestaoAustralia("Admin_aus", "123", "Admin")
    
    # O mesmo serviço registra todos eles
    auth.registrar(aluno)
    auth.registrar(jogador)
    auth.registrar(candidato)
    auth.registrar(gestor_aus)

    # Verifica se os escopos são mantidos no login
    logado_aluno = auth.login("Gabriel Soares", "Gabriel Soares")
    assert logado_aluno.escopo == "CACO_ESTUDANTE"
    assert hasattr(logado_aluno, "ra")
    assert logado_aluno.id == aluno.id 

    logado_jogador = auth.login("Leo_bct", "EuSouOLeo")
    assert logado_jogador.escopo == "BOTC_JOGADOR"

    logado_gestor = auth.login("Admin_aus", "123")
    assert logado_gestor.escopo == "AUSTRALIA_GESTAO,AUSTRALIA_ELEITOR"

def testa_adicionar_multiplos_escopos_com_sujeira() -> None:
    """Verifica se o método adicionar_escopo aplica split, strip, remove duplicatas e ordena."""
    # Teste 1: Um jogador simples ganhando múltiplos escopos
    jogador = JogadorBOTC("jogador1", "123", "Jogador Um")
    jogador.adicionar_escopo(" CACO_ESTUDANTE,  BOTC_JOGADOR , NOVO_ESCOPO ")
    assert jogador.escopo == "BOTC_JOGADOR,CACO_ESTUDANTE,NOVO_ESCOPO"

    # Teste 2: Um perfil que JÁ possui múltiplos escopos nativos (Gestão Austrália)
    gestor = GestaoAustralia("admin_aus", "123", "Admin")
    # O escopo original é "AUSTRALIA_GESTAO,AUSTRALIA_ELEITOR"
    # Vamos adicionar um novo e repetir um que já existe
    gestor.adicionar_escopo("NOVO_ESCOPO_ADMIN, AUSTRALIA_ELEITOR")
    
    # Valida se a classe base juntou tudo perfeitamente sem repetir
    assert gestor.escopo == "AUSTRALIA_ELEITOR,AUSTRALIA_GESTAO,NOVO_ESCOPO_ADMIN"

def testa_adicionar_escopo_com_ra_vinculado() -> None:
    """Garante que a passagem de RA no adicionar_escopo atualize o atributo do usuário."""
    jogador = JogadorBOTC("jogador_ra", "123", "Jogador com RA")
    
    # Adiciona o escopo de estudante e vincula o RA
    jogador.adicionar_escopo("CACO_ESTUDANTE", ra=112233)
    
    assert jogador.escopo == "BOTC_JOGADOR,CACO_ESTUDANTE"
    assert hasattr(jogador, "ra")
    assert jogador.ra == 112233

def testa_login_via_ra(auth: ServicoAutenticacao) -> None:
    """Verifica se estudantes do CACo conseguem autenticar utilizando o RA como login."""
    aluno = EstudanteCACo("caiolima", "senha123", "Caio Lima", 288808)
    auth.registrar(aluno)
    
    # Faz login passando o RA como string em vez do username 'caiolima'
    logado = auth.login("288808", "senha123")
    assert logado.id == aluno.id
    assert logado.escopo == "CACO_ESTUDANTE"

def testa_bloqueia_username_duplicado(auth: ServicoAutenticacao) -> None:
    """Um usuário não pode ter o mesmo login mesmo em escopos diferentes"""
    auth.registrar(EstudanteCACo("samuel", "123", "Samuel", 5))

    with pytest.raises(ValueError, match="já existente"):
        auth.registrar(JogadorBOTC("samuel", "213", "Samuel Impostor"))

def testa_bloqueia_ra_duplicado(auth: ServicoAutenticacao) -> None:
    """Um usuário não pode ter o mesmo RA mesmo em escopos diferentes"""
    auth.registrar(EstudanteCACo("samuel", "123", "Samuel", 5))

    with pytest.raises(ValueError, match="já existente"):
        auth.registrar(EstudanteCACo("outro", "456", "Outro Aluno", 5))

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

def testa_mesclar_escopos_usuario_existente(auth: ServicoAutenticacao) -> None:
    """Testa a lógica de adicionar novo escopo caso o usuário registre novamente com o mesmo username."""
    # 1. Cria usuário normal
    jogador = JogadorBOTC("jogador_hibrido", "senha123", "Hibrido")
    auth.registrar(jogador)
    
    # 2. Tenta registrar o mesmo username, mas agora como Eleitor da Austrália
    novo_papel = CandidatoAustralia("jogador_hibrido", "senha123", "Hibrido")
    auth.registrar(novo_papel)
    
    # Valida se o banco apenas atualizou os escopos do objeto existente
    logado = auth.login("jogador_hibrido", "senha123")
    assert logado.escopo == "AUSTRALIA_CANDIDATO,BOTC_JOGADOR"

def testa_mesclar_escopos_usuario_existente_com_ra(auth: ServicoAutenticacao) -> None:
    """Testa adicionar escopo de Estudante CACo (com RA) a um usuário já existente."""
    jogador = JogadorBOTC("aluno_hibrido", "senha123", "Hibrido RA")
    auth.registrar(jogador)
    
    # Registra a mesma conta, mas agora injetando papel de estudante CACo (que exige RA)
    estudante = EstudanteCACo("aluno_hibrido", "senha123", "Hibrido RA", 999999)
    auth.registrar(estudante)
    
    # Verifica se o RA foi salvo no objeto existente e se o mapa de logins aceita o RA
    logado_por_ra = auth.login("999999", "senha123")
    assert logado_por_ra.username == "aluno_hibrido"
    assert "CACO_ESTUDANTE" in logado_por_ra.escopo

def testa_mesclar_escopos_falha_ra_duplicado_ou_senha_errada(auth: ServicoAutenticacao) -> None:
    """Garante que a mescla de escopos falhe se a senha for errada ou se o RA colidir."""
    jogador1 = JogadorBOTC("user1", "senha1", "User 1")
    estudante2 = EstudanteCACo("user2", "senha2", "User 2", 111111)
    
    auth.registrar(jogador1)
    auth.registrar(estudante2)
    
    # Tenta mesclar no user1 usando senha errada
    falso_estudante = EstudanteCACo("user1", "senha_errada", "User 1", 222222)
    with pytest.raises(ValueError, match="já existente"):
        auth.registrar(falso_estudante)
        
    # Tenta mesclar no user1, com senha certa, mas injetando um RA que já pertence ao user2
    conflito_ra = EstudanteCACo("user1", "senha1", "User 1", 111111)
    with pytest.raises(ValueError, match="RA 111111 já existente"):
        auth.registrar(conflito_ra)