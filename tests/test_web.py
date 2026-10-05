import pytest
from fastapi.testclient import TestClient
from src.main import app

# Inicializa o cliente de testes simulando um navegador
client = TestClient(app)

def test_pagina_raiz_redireciona_para_login():
    """A raiz do site ('/') deve renderizar a tela de login."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Sistema de votação" in response.text
    assert "Identificação (RA/Usuário)" in response.text

def test_acesso_negado_ao_dashboard_sem_login():
    """Tentar acessar o painel sem um cookie de sessão válido retorna 401 ou expulsa."""
    response = client.get("/dashboard", allow_redirects=False)
    # A nossa dependência levanta um HTTPException 401
    assert response.status_code == 401 

def test_fluxo_login_sucesso():
    """Testa se o usuário mockado consegue logar e se recebe um cookie de sessão."""
    dados_login = {
        "username": "caio",
        "senha": "senha123"
    }
    
    # Faz o POST no formulário de login (sem seguir o redirecionamento automático)
    response_login = client.post("/login", data=dados_login, allow_redirects=False)
    
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
    response_cadastro = client.post("/cadastro", data=dados_cadastro, allow_redirects=False)
    assert response_cadastro.status_code == 302 # Redireciona para o dashboard
    
    # Acessa o dashboard usando os cookies ganhos no cadastro
    cookies = response_cadastro.cookies
    response_dashboard = client.get("/dashboard", cookies=cookies)
    
    html = response_dashboard.text
    assert response_dashboard.status_code == 200
    
    # Verifica se a variável do Jinja renderizou o nome corretamente
    assert "Bem-vindo, Teste Silva!" in html
    
    # Verifica o roteamento polimórfico
    # Como ele é estudante do CACo, NÃO deve ver a Eleição da Austrália
    assert "Eleição Federal 2026" not in html
    # Mas DEVE ver a assembleia
    assert "Assembleia CACo" in html or "Pauta" in html

def test_roteamento_polimorfico_caio_australia():
    """Verifica se o Caio (cadastrado no main.py como EleitorAustrália) só vê sua eleição."""
    # Simula o cookie já existente sem precisar fazer o POST do login
    cookies = {"sessao_usuario": "caio"}
    
    response = client.get("/dashboard", cookies=cookies)
    html = response.text
    
    assert "Eleição Federal 2026" in html
    assert "Assembleia CACo" not in html
    assert "Blood on the Clocktower" not in html

def test_acesso_bloqueado_ao_painel_admin():
    """Garante que usuários comuns (como o Caio, EleitorAustralia) não possam acessar a rota /admin."""
    cookies = {"sessao_usuario": "caio"}
    response = client.get("/admin", cookies=cookies, allow_redirects=False)
    
    # O redirecionamento (302) joga o usuário de volta para o Dashboard, pois ele não é GESTAO nem STORYTELLER
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"

def test_acesso_liberado_ao_painel_admin():
    """Garante que a Gestão (Julia) consiga acessar o painel administrativo."""
    cookies = {"sessao_usuario": "julia"}
    response = client.get("/admin", cookies=cookies)
    
    assert response.status_code == 200
    assert "Gerenciar Votações" in response.text