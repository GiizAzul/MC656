import pytest
from fastapi.testclient import TestClient
from src.main import app

# Inicializa o cliente de testes simulando um navegador
client = TestClient(app)

# Testes padrões de interface
def test_pagina_raiz_redireciona_para_login():
    """A raiz do site ('/') deve renderizar a tela de login."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Sistema de votação" in response.text
    assert "Identificação (RA/Usuário)" in response.text

def test_acesso_negado_ao_dashboard_sem_login():
    """Tentar acessar o painel sem um cookie de sessão válido retorna 302 ou expulsa."""
    response = client.get("/dashboard", follow_redirects=False)
    # A dependência levanta uma exceção de redirecionamento com código forçado 302
    assert response.status_code == 302

def test_fluxo_login_sucesso():
    """Testa se o usuário mockado consegue logar e se recebe um cookie de sessão."""
    dados_login = {
        "username": "caio",
        "senha": "senha123"
    }
    
    # Faz o POST no formulário de login (sem seguir o redirecionamento automático)
    response_login = client.post("/login", data=dados_login, follow_redirects=False)
    
    # O servidor deve responder com 302 (Found) redirecionando para o Dashboard
    assert response_login.status_code == 302
    assert response_login.headers["location"] == "/dashboard"
    
    # O cookie de sessão deve ter sido definido no navegador simulado
    assert "sessao_usuario" in response_login.cookies
    assert response_login.cookies["sessao_usuario"] == "caio"

def test_fluxo_login_senha_incorreta():
    """Testa se uma senha incorreta recarrega a tela com mensagem de erro."""
    dados_login = {
        "username": "caio",
        "senha": "senha_errada_aqui"
    }
    
    response = client.post("/login", data=dados_login)
    
    assert response.status_code == 200 # Continua na mesma página
    assert "Erro: Senha incorreta." in response.text

def test_fluxo_cadastro_e_acesso_dashboard():
    """Simula o cadastro de um Estudadante do CACo e acesso à tela correta."""
    dados_cadastro = {
        "tipo_conta": "CACO_ESTUDANTE",
        "nome_real": "Teste Silva",
        "username": "testesilva",
        "senha": "123",
        "senha_confirma": "123",
        "ra": "654321"
    }
    
    # Realiza o cadastro
    response_cadastro = client.post("/cadastro", data=dados_cadastro, follow_redirects=False)
    assert response_cadastro.status_code == 302 # Redireciona para o dashboard
    
    # Acessa o dashboard usando os cookies ganhos no cadastro
    client.cookies.update(response_cadastro.cookies)
    response_dashboard = client.get("/dashboard")
    
    html = response_dashboard.text
    assert response_dashboard.status_code == 200
    
    # Verifica se a variável do Jinja renderizou o nome corretamente
    assert "Bem-vindo, Teste Silva!" in html
    
    # Verifica o roteamento polimórfico
    # Como ele é estudante do CACo, NÃO deve ver a Eleição da Austrália
    assert "Eleição Federal 2026" not in html
    # Mas DEVE ver a assembleia
    assert "Assembleia CACo" in html or "Pauta" in html

    # Limpa os cookies para os próximos testes
    client.cookies.clear()

def test_roteamento_polimorfico_caio_australia():
    """Verifica se o Caio (cadastrado no main.py como EleitorAustrália) só vê sua eleição."""
    # Simula o cookie já existente sem precisar fazer o POST do login
    client.cookies.set("sessao_usuario", "caio")
    
    response = client.get("/dashboard")
    html = response.text
    
    assert "Eleição Federal 2026" in html
    assert "Assembleia CACo" not in html
    assert "Blood on the Clocktower" not in html

def test_acesso_bloqueado_ao_painel_admin():
    """Garante que usuários comuns (como o Caio, EleitorAustralia) não possam acessar a rota /admin."""
    client.cookies.set("sessao_usuario", "caio")
    response = client.get("/admin", follow_redirects=False)
    
    # O redirecionamento (302) joga o usuário de volta para o Dashboard, pois ele não é GESTAO nem STORYTELLER
    assert response.status_code in  [302,307]
    assert response.headers["location"] == "/dashboard"

    client.cookies.clear()


def test_acesso_liberado_ao_painel_admin():
    """Garante que a Gestão (Julia) consiga acessar o painel administrativo."""
    client.cookies.set("sessao_usuario", "julia")
    response = client.get("/admin")
    
    assert response.status_code == 200
    assert "Gerenciar Votações" in response.text

    client.cookies.clear()

def test_acesso_logout():
    """Testa se o botão de logout apaga os cookies e redireciona."""
    client.cookies.set("sessao_usuario", "caio")
    response = client.get("/logout", follow_redirects=False)
    
    assert response.status_code in [302,307]
    assert response.headers["location"] == "/"
    
    # A resposta de um logout deleta o cookie setando sua data de validade para o passado
    # ou setando valor vazio.
    cookie_str = response.headers.get("set-cookie", "")
    assert "sessao_usuario" in cookie_str 
    assert "expires" in cookie_str or "Max-Age=0" in cookie_str

def test_rota_votar_australia():
    """Simula o envio de uma cédula australiana ordenando os candidatos numericamente."""
    client.cookies.set("sessao_usuario", "caio")
    
    # Simula o formulário web onde o usuário digitou as posições 1, 2 e 3
    dados_voto = {
        "posicao_Ana": "1",
        "posicao_Beto": "2",
        "posicao_Caio": "3"
    }
    response = client.post("/australia/votar", data=dados_voto)
    
    assert response.status_code == 200
    assert "voto registrado" in response.text.lower()
    client.cookies.clear()
    
def test_rota_votar_caco():
    """Simula o envio de um voto de assembleia (Aprovar)."""
    client.cookies.set("sessao_usuario", "julia")
    # A eleição precisa estar iniciada para o voto ser aceito
    client.post("/caco/iniciar") 
    
    dados_voto = {"opcao": "APROVAR"}
    response = client.post("/caco/votar", data=dados_voto)
    
    assert response.status_code == 200
    assert "Seu voto na assembleia foi contabilizado" in response.text
    client.cookies.clear()

def test_rota_votar_botc():
    """Simula a ação de levantar a mão no BoTC."""
    client.cookies.set("sessao_usuario", "leo")
    
    dados_voto = {"acao": "levantar_mao"}
    response = client.post("/botc/votar", data=dados_voto)
    
    assert response.status_code == 200
    assert "Ação registrada" in response.text
    client.cookies.clear()

def test_dependencia_usuario_inexistente_no_mapa():
    """Testa se a dependência lança 302 caso o cookie exista mas o username não esteja no mapa."""
    client.cookies.set("sessao_usuario", "username_que_nao_existe")
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    client.cookies.clear()

def test_dependencia_cookie_vazio():
    """Testa o acesso sem o cookie."""
    client.cookies.clear()
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302

# Testes de auth_router.py 
def test_cadastro_senhas_diferentes():
    """Tenta cadastrar mas digita senhas divergentes."""
    dados = {
        "tipo_conta": "AUSTRALIA_ELEITOR",
        "nome_real": "Erro Senha",
        "username": "errosenha",
        "senha": "123",
        "senha_confirma": "321" # Diferente
    }
    response = client.post("/cadastro", data=dados)
    assert response.status_code == 200
    assert "Senhas não conferem" in response.text

def test_cadastro_tipo_desconhecido():
    """Tenta cadastrar enviando um tipo de conta malicioso/inexistente."""
    dados = {
        "tipo_conta": "TIPO_HACKER",
        "nome_real": "Hacker",
        "username": "hacker123",
        "senha": "123",
        "senha_confirma": "123"
    }
    response = client.post("/cadastro", data=dados)
    assert response.status_code == 200
    assert "Tipo de conta desconhecido" in response.text

def test_cadastro_estudante_ra_invalido():
    """Tenta cadastrar estudante sem passar o RA."""
    dados = {
        "tipo_conta": "CACO_ESTUDANTE",
        "nome_real": "Sem RA",
        "username": "semra",
        "senha": "123",
        "senha_confirma": "123",
        "ra": "" # Vazio
    }
    response = client.post("/cadastro", data=dados)
    assert response.status_code == 200
    assert "RA inválido" in response.text

def test_fraude_de_escopos_cross_router():
    """Testa se as verificações de escopo expulsam intrusos."""
    client.cookies.set("sessao_usuario", "caio") # Austrália tentando acessar CACo e BOTC
    assert client.post("/caco/votar", data={"opcao": "APROVAR"}, follow_redirects=False).status_code in [302, 307]
    assert client.post("/caco/iniciar", follow_redirects=False).status_code in [302, 307]
    assert client.post("/caco/encerrar", follow_redirects=False).status_code in [302, 307]
    assert client.get("/caco/resultados", follow_redirects=False).status_code in [403]
    assert client.post("/botc/registrar", data={"nomeado": "x", "num_votos": 1}, follow_redirects=False).status_code in [302, 307]
    assert client.post("/botc/apurar", follow_redirects=False).status_code in [302, 307]
    
    client.cookies.set("sessao_usuario", "julia") # CACo tentando acessar Austrália
    assert client.post("/australia/votar", data={"posicao_Candidato A": "1"}, follow_redirects=False).status_code in [302, 307]
    assert client.get("/botc/partida", follow_redirects=False).status_code in [302, 307]
    client.cookies.clear()

# Testes caco_router.py
def test_caco_acesso_deslogado():
    """Tentativa de acessar a tela da assembleia sem login."""
    client.cookies.clear()
    response = client.get("/caco/assembleia", follow_redirects=False)
    assert response.status_code == 302 # Redireciona para login

def test_caco_acoes_gestao():
    """Testa os botões de Iniciar, Encerrar e Resultados acessados por alguém da Gestão."""
    client.cookies.set("sessao_usuario", "julia")

    res_iniciar = client.post("/caco/iniciar")
    assert res_iniciar.status_code == 200

    res_resultados = client.get("/caco/resultados")
    # Verifica a nova interface de barras de progresso
    assert "Total de Votos Registrados" in res_resultados.text 

    res_encerrar = client.post("/caco/encerrar")
    assert "Votação da Assembleia encerrada" in res_encerrar.text
    client.cookies.clear()

def test_caco_acoes_gestao_bloqueadas():
    """Garante que um Estudante ou Eleitor da Austrália não pode iniciar a assembleia."""
    client.cookies.set("sessao_usuario", "caio") # EleitorAustrália
    # O sistema redireciona intrusos para a página de login (302/307)
    response = client.post("/caco/iniciar", follow_redirects=False)
    assert response.status_code in [302, 307] 
    client.cookies.clear()

def test_cadastro_todos_os_tipos_restantes_e_autorizacao_caco():
    """Cadastra os tipos restantes, faz login real e testa se ganhou permissão."""
    tipos_restantes = [
        ("CACO_GESTAO", "novo_gestor_exaustivo"), 
        ("AUSTRALIA_CANDIDATO", "novo_candidato_exaustivo"), 
        ("BOTC_STORYTELLER", "novo_storyteller_exaustivo")
    ]
    for tipo, user in tipos_restantes:
        dados = {
            "tipo_conta": tipo,
            "nome_real": f"Teste {user}",
            "username": user,
            "senha": "123",
            "senha_confirma": "123"
        }
        res = client.post("/cadastro", data=dados, follow_redirects=False)
        assert res.status_code in [302, 307]

    # Faz o login de verdade para o servidor validar os cookies da sessão
    res_login = client.post("/login", data={"username": "novo_gestor_exaustivo", "senha": "123"}, follow_redirects=False)
    client.cookies.update(res_login.cookies)
    
    # Tenta iniciar a eleição para ter certeza que foi reconhecido
    res_caco = client.post("/caco/iniciar")
    assert res_caco.status_code == 200
    assert "sucesso" in res_caco.text.lower() or "andamento" in res_caco.text.lower()
    client.cookies.clear()    

def test_caco_router_excecoes_internas():
    """Aciona os blocos 'except Exception' do caco_router."""
    client.cookies.set("sessao_usuario", "julia")
    # Inicia e tenta iniciar de novo (Gera RuntimeError)
    client.post("/caco/iniciar")
    res_iniciar2 = client.post("/caco/iniciar")
    assert "já está em andamento" in res_iniciar2.text.lower()
    
    # Tenta votar com enum quebrado (Gera KeyError/Exception)
    res_voto_errado = client.post("/caco/votar", data={"opcao": "FRAUDE"})
    assert "erro" in res_voto_errado.text.lower() or "fraude" in res_voto_errado.text
    
    # Encerra e tenta encerrar de novo (Gera RuntimeError)
    client.post("/caco/encerrar")
    res_encerrar2 = client.post("/caco/encerrar")
    assert "não existe" in res_encerrar2.text.lower() or "encerrada" in res_encerrar2.text.lower()
    client.cookies.clear()

# Testes botc_router.py
def test_botc_acesso_deslogado():
    client.cookies.clear()
    response = client.get("/botc/partida", follow_redirects=False)
    assert response.status_code == 302 # Redireciona

def test_botc_acoes_storyteller():
    """Testa o registro de votos e a apuração da forca feitos pelo mestre."""
    client.cookies.set("sessao_usuario", "leo") # leo é Jogador, precisaremos de um storyteller
    # Cadastrando um Mestre temporário para o teste
    dados_mestre = {
        "tipo_conta": "BOTC_STORYTELLER",
        "nome_real": "Mestre Supremo",
        "username": "mestresup",
        "senha": "123",
        "senha_confirma": "123"
    }
    client.post("/cadastro", data=dados_mestre)
    client.cookies.set("sessao_usuario", "mestresup")
    
    res_registro = client.post("/botc/registrar", data={"nomeado": "Leo", "num_votos": 3})
    assert "3 votos registrados" in res_registro.text
    
    res_apurar = client.post("/botc/apurar")
    assert "executado" in res_apurar.text
    client.cookies.clear()

def test_botc_acoes_storyteller_bloqueadas():
    """Um jogador não pode apurar votos do BoTC."""
    # Cadastrando um jogador temporário para garantir que ele existe no banco do teste
    dados_jogador = {
        "tipo_conta": "BOTC_JOGADOR",
        "nome_real": "Leo Jogador",
        "username": "leojogador",
        "senha": "123",
        "senha_confirma": "123"
    }
    client.post("/cadastro", data=dados_jogador)
    client.cookies.set("sessao_usuario", "leojogador") 
    
    response = client.post("/botc/apurar")
    assert response.status_code == 403
    assert "Apenas o Storyteller pode" in response.text
    client.cookies.clear()

# Testes australia_router.py
def test_australia_acesso_deslogado():
    client.cookies.clear()
    response = client.get("/australia/votar", follow_redirects=False)
    assert response.status_code == 302 # Redireciona