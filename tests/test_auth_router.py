from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.autenticacao.caco import EstudanteCACo
from src.main import app


@pytest.fixture
def client():
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def app_state_mock():
    return app.state


@patch("src.routers.auth_router.UsuarioFactory.criar")
def test_rota_cadastro_delega_para_factory(mock_criar, client, app_state_mock):
    # Configura o retorno da Factory mockada
    mock_usuario = EstudanteCACo("giovana", "senha123", "Giovana", 123456)
    mock_criar.return_value = mock_usuario

    response = client.post(
        "/cadastro",
        data={
            "tipo_conta": "CACO_ESTUDANTE",
            "username": "giovana",
            "senha": "password123",
            "senha_confirma": "password123",
            "nome_real": "Giovana",
            "ra": "123456",
        },
        follow_redirects=False,
    )

    mock_criar.assert_called_once_with(
        "CACO_ESTUDANTE", "giovana", "password123", "Giovana", "123456"
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"
    client.cookies.clear()


def test_australia_rejeita_float_com_mensagem_correta(client):
    """Garante que números decimais como 3.00000000000001 disparam erro de posição inválida."""
    client.post(
        "/cadastro",
        data={
            "tipo_conta": "AUSTRALIA_ELEITOR",
            "nome_real": "Eleitor Float",
            "username": "eleitor_float",
            "senha": "123",
            "senha_confirma": "123",
        },
    )
    client.cookies.set("sessao_usuario", "eleitor_float")

    dados_voto = {
        "posicao_Candidato A": "1",
        "posicao_Candidato B": "2",
        "posicao_Candidato C": "3.00000000000001",
    }
    response = client.post("/australia/votar", data=dados_voto)
    assert response.status_code == 200
    assert "números inteiros positivos" in response.text.lower()
    client.cookies.clear()


def test_mesmo_username_pode_cadastrar_novo_escopo_ou_adicionar_escopo(client):
    """Permite que um usuário cadastrado em um escopo adicione outro escopo à mesma conta."""
    client.post(
        "/cadastro",
        data={
            "tipo_conta": "AUSTRALIA_ELEITOR",
            "nome_real": "Multi User",
            "username": "multi_user",
            "senha": "123",
            "senha_confirma": "123",
        },
    )
    # Cadastra novamente com o mesmo username e senha em outro escopo (BOTC_JOGADOR)
    res2 = client.post(
        "/cadastro",
        data={
            "tipo_conta": "BOTC_JOGADOR",
            "nome_real": "Multi User",
            "username": "multi_user",
            "senha": "123",
            "senha_confirma": "123",
        },
        follow_redirects=False,
    )
    assert res2.status_code == 302

    # Usa também a rota /adicionar-escopo logado para adicionar CACO_ESTUDANTE
    client.cookies.set("sessao_usuario", "multi_user")
    res3 = client.post(
        "/adicionar-escopo",
        data={"tipo_conta": "CACO_ESTUDANTE", "ra": "777888"},
        follow_redirects=False,
    )
    assert res3.status_code == 302

    perfil = client.get("/api/me").json()
    assert "AUSTRALIA" in perfil["escopo"]
    assert "BOTC" in perfil["escopo"]
    assert "CACO" in perfil["escopo"]
    client.cookies.clear()


def test_botc_alternar_mao_json_sem_tela_sucesso(client):
    """Testa levantar e abaixar a mão via JSON sem redirecionar para sucesso.html."""
    client.cookies.set("sessao_usuario", "leo")
    res_up = client.post(
        "/botc/votar",
        data={"acao": "levantar_mao"},
        headers={"Accept": "application/json"},
    )
    assert res_up.status_code == 200
    assert res_up.json()["mao_levantada"] is True

    res_down = client.post(
        "/botc/votar",
        data={"acao": "abaixar_mao"},
        headers={"Accept": "application/json"},
    )
    assert res_down.status_code == 200
    assert res_down.json()["mao_levantada"] is False
    client.cookies.clear()

def test_adicionar_escopo_erro_e_cedula_em_branco_australia(client):
    # 1. Cobre except de /adicionar-escopo
    client.cookies.set("sessao_usuario", "caio")
    res_err = client.post("/adicionar-escopo", data={"tipo_conta": "CACO_ESTUDANTE", "ra": "invalido"})
    assert res_err.status_code == 200

    # 2. Cobre linhas 50 e 53 de base.py (re-cadastro com RA já existente e adição de RA via re-cadastro)
    client.post("/cadastro", data={"tipo_conta": "AUSTRALIA_ELEITOR", "nome_real": "U", "username": "u_ra", "senha": "1", "senha_confirma": "1"})
    client.post("/cadastro", data={"tipo_conta": "CACO_ESTUDANTE", "nome_real": "U", "username": "u_ra", "senha": "1", "senha_confirma": "1", "ra": "919191"})
    client.post("/cadastro", data={"tipo_conta": "AUSTRALIA_ELEITOR", "nome_real": "U2", "username": "u_ra2", "senha": "1", "senha_confirma": "1"})
    res_ra_dup = client.post("/cadastro", data={"tipo_conta": "CACO_ESTUDANTE", "nome_real": "U2", "username": "u_ra2", "senha": "1", "senha_confirma": "1", "ra": "919191"})
    assert res_ra_dup.status_code == 200

    # 3. Cobre linhas 125 (campo vazio) e 138 (incompleto) de australia_router com eleitor virgem
    client.cookies.set("sessao_usuario", "u_ra2")
    res_aus = client.post("/australia/votar", data={"posicao_Candidato A": "", "posicao_Candidato B": "1"})
    assert res_aus.status_code == 200
    assert "Você ranqueou" in res_aus.text
    client.cookies.clear()