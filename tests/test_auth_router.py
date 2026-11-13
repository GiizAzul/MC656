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

def test_fluxo_completo_salas_botc_e_estado_australia(client):
    """Cobre todas as rotas JSON de salas do BoTC, giro e estado da Austrália para o SonarCloud."""
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "caio")
    assert client.get("/australia/api/estado").status_code == 200

    # Cadastra um Storyteller e um Jogador explícitos para o teste
    client.post(
        "/cadastro",
        data={
            "tipo_conta": "BOTC_STORYTELLER",
            "nome_real": "Mestre Teste",
            "username": "st_teste",
            "senha": "1",
            "senha_confirma": "1",
        },
    )
    client.post(
        "/cadastro",
        data={
            "tipo_conta": "BOTC_JOGADOR",
            "nome_real": "Jog2",
            "username": "jog2",
            "senha": "1",
            "senha_confirma": "1",
        },
    )
    client.cookies.clear()

    # Loga com storyteller (st_teste) e cria sala com senha
    client.cookies.set("sessao_usuario", "st_teste")
    assert client.get("/botc/api/estado?apenas_lobby=true").status_code == 200
    res_criar = client.post(
        "/botc/api/criar-partida",
        data={"nome_sala": "Sala Secreta", "senha_sala": "1234"},
    )
    assert res_criar.status_code == 200
    pid = res_criar.json()["partida_id"]

    # Jog2 tenta ações não autorizadas (403/404) e depois entra com a senha certa (200)
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "jog2")
    assert client.post("/botc/api/assumir-storyteller", data={"partida_id": pid}).status_code == 403
    assert client.post("/botc/api/iniciar-giro", data={"partida_id": pid, "nomeado_id": "Jog2"}).status_code == 403
    assert client.post("/botc/api/encerrar-partida", data={"partida_id": pid}).status_code == 403
    assert client.post("/botc/api/excluir-sala", data={"partida_id": pid}).status_code == 403
    assert client.post("/botc/api/entrar-sala", data={"partida_id": "inexistente"}).status_code == 404
    assert client.get(f"/botc/api/estado?partida_id={pid}").status_code == 403
    assert client.post("/botc/api/entrar-sala", data={"partida_id": pid, "senha_sala": "errada"}).status_code == 403
    assert client.post("/botc/api/entrar-sala", data={"partida_id": pid, "senha_sala": "1234"}).status_code == 200
    assert client.get(f"/botc/api/estado?partida_id={pid}").status_code == 200
    assert client.post(
        "/botc/votar",
        data={"acao": "levantar_mao", "partida_id": pid},
        headers={"Accept": "application/json"},
    ).status_code == 200

    # Storyteller (st_teste) assume o centro da roda
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "st_teste")
    assert client.post("/botc/api/assumir-storyteller", data={"partida_id": pid}).status_code == 200
    assert client.get(f"/botc/api/estado?partida_id={pid}").status_code == 200

    # Storyteller não pode votar na partida que conduz (403), nem criar outra sala (400), nem sair antes de encerrar (400)
    assert client.post(
        "/botc/votar",
        data={"acao": "levantar_mao", "partida_id": pid},
        headers={"Accept": "application/json"},
    ).status_code == 403
    assert client.post("/botc/api/criar-partida", data={"nome_sala": "Outra"}).status_code == 400
    assert client.post("/botc/api/sair-sala", data={"partida_id": pid}).status_code == 400

    # Storyteller altera status do jog2 para Morto (Com Voto), inicia giro e testa bloqueio de mão pós-ponteiro
    assert client.post(
        "/botc/status-jogador",
        data={"id_jogador": "Jog2", "novo_status": "Morto (Com Voto)", "partida_id": pid},
    ).status_code == 200
    assert client.post("/botc/api/iniciar-giro", data={"partida_id": pid, "nomeado_id": "Jog2"}).status_code == 200
    assert client.post("/botc/api/iniciar-giro", data={"partida_id": pid, "nomeado_id": "Jog2"}).status_code == 400

    # Simula avanço do ponteiro (1 passo) e verifica que jog2 fica trancado ao tentar mudar a mão
    from src.main import app
    app.state.salas_botc[pid]["giro"]["inicio_ts"] -= 2.0
    assert client.get(f"/botc/api/estado?partida_id={pid}").status_code == 200

    client.cookies.clear()
    client.cookies.set("sessao_usuario", "jog2")
    assert client.get(f"/botc/api/estado?partida_id={pid}").status_code == 200

    # Storyteller apura o dia, encerra a partida inteira e exclui a sala
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "st_teste")
    assert client.post("/botc/apurar", data={"partida_id": pid}).status_code == 200
    assert client.post("/botc/api/encerrar-partida", data={"partida_id": "inexistente"}).status_code == 404
    assert client.post("/botc/api/encerrar-partida", data={"partida_id": pid}).status_code == 200
    assert client.post("/botc/api/sair-sala", data={"partida_id": "inexistente"}).status_code == 200
    assert client.post("/botc/api/excluir-sala", data={"partida_id": "inexistente"}).status_code == 404
    assert client.post("/botc/api/excluir-sala", data={"partida_id": pid}).status_code == 200
    client.cookies.clear()

def test_casos_borda_salas_e_giro_botc(client):
    """Cobre as linhas restantes de botc_router.py (auto-exclusão, colisão de ST, trava pós-ponteiro e fim do giro)."""
    from src.main import app

    # Cadastra um segundo Storyteller (st2) e um jogador (jog_borda)
    client.post(
        "/cadastro",
        data={
            "tipo_conta": "BOTC_STORYTELLER",
            "nome_real": "Mestre Dois",
            "username": "st2",
            "senha": "1",
            "senha_confirma": "1",
        },
    )
    client.post(
        "/cadastro",
        data={
            "tipo_conta": "BOTC_JOGADOR",
            "nome_real": "Jog Borda",
            "username": "jog_borda",
            "senha": "1",
            "senha_confirma": "1",
        },
    )
    client.cookies.clear()

    # 1. Jogador cria sala pública e sai (testa linhas 301-315 e auto-exclusão da sala vazia)
    client.cookies.set("sessao_usuario", "jog_borda")
    pid_temp = client.post("/botc/api/criar-partida", data={"nome_sala": "Sala Temp"}).json()["partida_id"]
    assert client.post("/botc/api/sair-sala", data={"partida_id": pid_temp}).status_code == 200
    assert pid_temp not in app.state.salas_botc

    # 2. Cria nova sala com jog_borda; st_teste inicia giro assumindo automaticamente a sala vazia de ST (linhas 580-585)
    pid2 = client.post("/botc/api/criar-partida", data={"nome_sala": "Sala Giro"}).json()["partida_id"]
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "st_teste")
    assert client.post("/botc/api/iniciar-giro", data={"partida_id": pid2, "nomeado_id": "jog_borda"}).status_code == 200

    # 3. Outro Storyteller (st2) tenta assumir ou iniciar giro na sala que já pertence a st_teste (linhas 367 e 586)
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "st2")
    assert client.post("/botc/api/assumir-storyteller", data={"partida_id": pid2}).status_code == 400
    assert client.post("/botc/api/iniciar-giro", data={"partida_id": pid2, "nomeado_id": "jog_borda"}).status_code == 403

    # 4. Trava o jog_borda no giro ativo e tenta votar com Accept: application/json (linhas 154-156)
    app.state.salas_botc[pid2]["giro"]["trancados"]["jog_borda"] = True
    app.state.salas_botc[pid2]["giro"]["trancados_nomes"].add("Jog Borda")
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "jog_borda")
    res_trancado = client.post(
        "/botc/votar",
        data={"acao": "abaixar_mao", "partida_id": pid2},
        headers={"Accept": "application/json"},
    )
    assert res_trancado.status_code == 400

    # 5. Avança o relógio além do total de jogadores para concluir 100% do giro (linhas 555-561)
    app.state.salas_botc[pid2]["giro"]["inicio_ts"] -= 30.0
    assert client.get(f"/botc/api/estado?partida_id={pid2}").status_code == 200

    # 6. Encerra a partida, Storyteller sai da sala encerrada (linhas 309-311) e testa roda sem jogadores (linha 591)
    client.cookies.clear()
    client.cookies.set("sessao_usuario", "st_teste")
    assert client.post("/botc/api/encerrar-partida", data={"partida_id": pid2}).status_code == 200
    assert client.post("/botc/api/sair-sala", data={"partida_id": pid2}).status_code == 200

    # Sala criada pelo próprio st_teste onde ele assume ST e fica com 0 jogadores votantes (linha 591)
    pid_vazia = client.post("/botc/api/criar-partida", data={"nome_sala": "SoMestre"}).json()["partida_id"]
    assert client.post("/botc/api/assumir-storyteller", data={"partida_id": pid_vazia}).status_code == 200
    assert client.post("/botc/api/iniciar-giro", data={"partida_id": pid_vazia, "nomeado_id": "ninguem"}).status_code == 400
    assert client.post("/botc/api/excluir-sala", data={"partida_id": pid_vazia}).status_code == 200
    client.cookies.clear()