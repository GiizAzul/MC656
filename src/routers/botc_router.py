from pathlib import Path
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.autenticacao.base import Usuario
from src.botc import (
    JogadorBotC,
    SistemaEleitoralBotC,
    StatusJogador,
)

from .dependencias import obter_usuario_logado

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/botc", tags=["BOTC"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _obter_salas_botc(app_state) -> dict:
    """Gerencia múltiplas partidas de BoTC. A sala 'principal' usa app_state.sistema_botc para compatibilidade com os testes."""
    if not hasattr(app_state, "salas_botc"):
        app_state.salas_botc = {}
    if "principal" not in app_state.salas_botc:
        app_state.salas_botc["principal"] = {
            "id": "principal",
            "nome": "Partida Principal — Ravenswood Bluff",
            "sistema": app_state.sistema_botc,
            "storyteller_id": None,
            "storyteller_nome": None,
            "senha": None,
            "autorizados": set(),
            "nomeados_hoje": set(),
            "maos": getattr(app_state, "maos_botc", {}),
            "giro": {
                "ativo": False,
                "nomeado_id": None,
                "nomeado_nome": None,
                "ordem_ids": [],
                "inicio_ts": 0.0,
                "passo_atual": -1,
                "trancados": {},
                "trancados_nomes": set(),
                "votos_computados": 0,
                "mensagem_final": "",
            },
        }
    else:
        app_state.salas_botc["principal"]["sistema"] = app_state.sistema_botc
    return app_state.salas_botc

def _eh_storyteller_da_sala(sala: dict, usuario: Usuario) -> bool:
    """Verifica se o usuário já assumiu explicitamente o papel de Storyteller titular desta partida."""
    return sala["storyteller_id"] == usuario.id

def _obter_ou_criar_jogador(
    sistema, 
    usuario: Usuario, 
    sala: dict | None = None
) -> JogadorBotC:
    """Garante que o usuário autenticado esteja registrado no sistema eleitoral BotC e registra o usuário como jogador votante apenas se ele não for o Storyteller desta partida."""
    if sala and _eh_storyteller_da_sala(sala, usuario):
        return None
    
    jogador = (
        sistema.obter_jogador(usuario.id)
        or sistema.obter_jogador(usuario.username)
        or sistema.obter_jogador(usuario.nome_real)
    )
    if not jogador:
        jogador = JogadorBotC(
            id_jogador=usuario.id,
            nome= usuario.username,
            status=StatusJogador.VIVO,
        )
        sistema.adicionar_jogador(jogador)
    return jogador


@router.get("/partida", response_class=HTMLResponse)
async def tela_partida(
    request: Request, 
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)]
):
    if "BOTC" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    salas = _obter_salas_botc(request.app.state)
    sala = salas["principal"]
    sistema = sala["sistema"]
    maos = sala["maos"]
    mao_levantada = maos.get(usuario.username, False)
    
    is_storyteller = "STORYTELLER" in usuario.escopo
    jogador_atual = _obter_ou_criar_jogador(sistema, usuario)

    jogadores_view = [
        {
            "id": jog.id_jogador,
            "nome": jog.nome,
            "status": jog.status.value,
            "peso": jog.calcular_peso_voto(),
        }
        for jog in sistema.jogadores.values()
        if jog.id_jogador != sala["storyteller_id"]
    ]

    return templates.TemplateResponse(
        name="botc.html",
        request=request,
        context={
            "jogadores": jogadores_view,
            "votos": getattr(sistema, "votos", {}),
            "is_storyteller": is_storyteller,
            "pode_votar": jogador_atual.pode_votar() if jogador_atual else False,
            "status_usuario": jogador_atual.status.value if jogador_atual else "STORYTELLER",
            "mao_levantada": mao_levantada,
            "maos_ativas": maos,
        },
    )


@router.post("/votar")
async def processar_voto_botc(
    request: Request,
    acao: str = Form(...),
    partida_id: str = Form("principal"),
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)] = None,
):
    salas = _obter_salas_botc(request.app.state)
    sala = salas.get(partida_id, salas["principal"])
    sistema = sala["sistema"]

    if not hasattr(request.app.state, "maos_botc"):
        request.app.state.maos_botc = sala["maos"]

    # Storyteller da partida não pode votar!
    if usuario is not None and sala["storyteller_id"] == usuario.id:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(
                {"erro": "Você é o Storyteller desta partida e não possui poder de voto."},
                status_code=403,
            )

    giro = sala["giro"]
    if giro.get("ativo") and usuario is not None:
        if usuario.id in giro.get("trancados", {}) or usuario.nome_real in giro.get("trancados_nomes", set()):
            if "application/json" in request.headers.get("accept", ""):
                return JSONResponse(
                    {"erro": "O ponteiro já passou por você! Seu voto foi computado e sua mão está travada."},
                    status_code=400,
                )
    
    mao_levantada = acao == "levantar_mao"
    if usuario is not None:
        sala["maos"][usuario.username] = mao_levantada
        sala["maos"][usuario.nome_real] = mao_levantada
        sala["maos"][usuario.id] = mao_levantada
        request.app.state.maos_botc[usuario.username] = mao_levantada

    if usuario is not None and "BOTC" in usuario.escopo:
        jogador = _obter_ou_criar_jogador(sistema, usuario)

        # Se a requisição vier via fetch/React (Accept: application/json), responde sem trocar de tela!
        if "application/json" in request.headers.get("accept", ""):
            total_maos = sum(1 for v in sala["maos"].values() if v)
            return JSONResponse({
                "status": "ok",
                "mao_levantada": mao_levantada,
                "total_maos": total_maos,
                "mensagem": "Ação registrada na roda da cidade.",
            })
        if jogador and not jogador.pode_votar():
            jogadores_view = [
                {"id": j.id_jogador, "nome": j.nome, "status": j.status.value, "peso": j.calcular_peso_voto()}
                for j in sistema.jogadores.values()
            ]
            return templates.TemplateResponse(
                name="botc.html",
                request=request,
                context={
                    "jogadores": jogadores_view,
                    "votos": getattr(sistema, "votos", {}),
                    "is_storyteller": "STORYTELLER" in usuario.escopo,
                    "pode_votar": False,
                    "status_usuario": jogador.status.value,
                    "erro": "Você está morto e já utilizou seu voto fantasma nesta partida.",
                },
            )

    return templates.TemplateResponse(
        name="sucesso.html",
        request=request,
        context={"mensagem": "Ação registrada na roda da cidade."},
    )


@router.post("/api/criar-partida")
async def criar_nova_partida_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    nome_sala: str = Form(...),
    senha_sala: str = Form(""),
):
    salas = _obter_salas_botc(request.app.state)
    # Usa timestamp/contador único para evitar colisão após deleções
    novo_id = f"partida_{int(time.time() * 1000)}"
    novo_sistema = SistemaEleitoralBotC()

    # Adiciona apenas quem criou a sala inicialmente como jogador (ele pode clicar em Assumir Storyteller depois se quiser)
    novo_sistema.adicionar_jogador(
        JogadorBotC(id_jogador=usuario.id, nome=usuario.username, status=StatusJogador.VIVO)
    )

    senha_limpa = senha_sala.strip() or None
    salas[novo_id] = {
        "id": novo_id,
        "nome": nome_sala.strip() or f"Partida #{len(salas) + 1}",
        "sistema": novo_sistema,
        "storyteller_id": None,
        "storyteller_nome": None,
        "senha": senha_limpa,
        "autorizados": {usuario.id},
        "nomeados_hoje": set(),
        "maos": {},
        "giro": {
            "ativo": False,
            "nomeado_id": None,
            "nomeado_nome": None,
            "ordem_ids": [],
            "inicio_ts": 0.0,
            "passo_atual": -1,
            "trancados": {},
            "trancados_nomes": set(),
            "votos_computados": 0,
            "mensagem_final": "",
        },
    }
    return JSONResponse({"status": "criada", "partida_id": novo_id})
@router.post("/api/entrar-sala")
async def entrar_sala_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    partida_id: str = Form(...),
    senha_sala: str = Form(""),
):
    salas = _obter_salas_botc(request.app.state)
    if partida_id not in salas:
        raise HTTPException(status_code=404, detail="Sala não encontrada.")
    sala = salas[partida_id]
    sala.setdefault("autorizados", set())

    if sala.get("senha") and usuario.id not in sala["autorizados"]:
        if senha_sala.strip() != sala["senha"]:
            raise HTTPException(status_code=403, detail="Senha da sala incorreta!")

    sala["autorizados"].add(usuario.id)
    return JSONResponse({"status": "ok", "partida_id": partida_id})


@router.post("/api/sair-sala")
async def sair_da_sala_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    partida_id: str = Form(...),
):
    salas = _obter_salas_botc(request.app.state)
    if partida_id not in salas or partida_id == "principal":
        return JSONResponse({"status": "ok", "partida_destino": "principal"})

    sala = salas[partida_id]
    sistema = sala["sistema"]

    # Remove o usuário se ele era jogador ou Storyteller
    sistema.jogadores.pop(usuario.id, None)
    sistema.jogadores.pop(usuario.username, None)
    sistema.jogadores.pop(usuario.nome_real, None)
    sala["maos"].pop(usuario.username, None)
    sala.get("autorizados", set()).discard(usuario.id)

    if sala["storyteller_id"] == usuario.id:
        sala["storyteller_id"] = None
        sala["storyteller_nome"] = None

    # Se não sobrou nenhum jogador E nenhum Storyteller, exclui a sala automaticamente!
    if len(sistema.jogadores) == 0 and sala["storyteller_id"] is None:
        salas.pop(partida_id, None)

    return JSONResponse({"status": "saiu", "partida_destino": "principal"})


@router.post("/api/excluir-sala")
async def excluir_sala_storyteller(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    partida_id: str = Form(...),
):
    salas = _obter_salas_botc(request.app.state)
    if partida_id == "principal":
        raise HTTPException(status_code=400, detail="A sala principal padrão não pode ser excluída.")
    if partida_id not in salas:
        raise HTTPException(status_code=404, detail="Sala não encontrada.")

    sala = salas[partida_id]
    if sala["storyteller_id"] != usuario.id:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller titular desta sala pode excluí-la.")

    salas.pop(partida_id, None)
    return JSONResponse({"status": "excluida", "partida_destino": "principal"})
    
@router.post("/api/assumir-storyteller")
async def assumir_storyteller_partida(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    partida_id: str = Form("principal"),
):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Você não possui o escopo BOTC_STORYTELLER.")

    salas = _obter_salas_botc(request.app.state)
    sala = salas.get(partida_id, salas["principal"])

    if sala["storyteller_id"] is not None and sala["storyteller_id"] != usuario.id:
        raise HTTPException(
            status_code=400,
            detail=f"Esta partida já possui um Storyteller ({sala['storyteller_nome']}). Cada partida só permite 1 Storyteller!",
        )

    sala["storyteller_id"] = usuario.id
    sala["storyteller_nome"] = usuario.username
    # Remove o Storyteller dos assentos votantes da borda da roda
    sala["sistema"].jogadores.pop(usuario.id, None)
    sala["sistema"].jogadores.pop(usuario.username, None)
    sala["sistema"].jogadores.pop(usuario.nome_real, None)

    return JSONResponse({"status": "ok", "storyteller_nome": sala["storyteller_nome"]})

@router.post("/registrar")
async def registrar_votos_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    nomeado: str = Form(...),
    num_votos: int = Form(...),
):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode registrar votos.")

    sistema = request.app.state.sistema_botc
    try:
        sistema.registrar_votacao(nomeado, num_votos)
    except ValueError as e:
        jogadores_view = [
            {"id": j.id_jogador, "nome": j.nome, "status": j.status.value, "peso": j.calcular_peso_voto()}
            for j in sistema.jogadores.values()
        ]
        return templates.TemplateResponse(
            name="botc.html",
            request=request,
            context={
                "jogadores": jogadores_view,
                "votos": getattr(sistema, "votos", {}),
                "is_storyteller": True,
                "pode_votar": True,
                "status_usuario": StatusJogador.VIVO.value,
                "erro": str(e),
            },
        )

    return templates.TemplateResponse(
        name="sucesso.html",
        request=request,
        context={"mensagem": f"{num_votos} votos registrados para {nomeado}."},
    )


@router.post("/modificador")
async def aplicar_modificador_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    id_jogador: str = Form(...),
    tipo_modificador: str = Form(...),
    fator: int = Form(3),
):
    """Permite ao Storyteller configurar modificadores ocultos em jogadores"""
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode configurar modificadores.")

    sistema = request.app.state.sistema_botc
    jogador = sistema.obter_jogador(id_jogador)
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    if tipo_modificador == "multiplicador":
        jogador.adicionar_multiplicador(fator=fator)
    elif tipo_modificador == "negativo":
        jogador.adicionar_negativador()
    elif tipo_modificador == "multiplicador_negativo":
        # Aplica multiplicador e inverte o sinal (ex: x3 -> -3)
        jogador.resetar_modificador()
        jogador.adicionar_multiplicador(fator=fator)
        jogador.adicionar_negativador()
    elif tipo_modificador == "nulo":
        jogador.anular_voto()
    elif tipo_modificador == "padrao":
        jogador.resetar_modificador()
    else:
        raise HTTPException(status_code=400, detail="Tipo de modificador desconhecido.")

    peso_final = jogador.calcular_peso_voto()
    return templates.TemplateResponse(
        name="sucesso.html",
        request=request,
        context={
            "mensagem": f"Modificador '{tipo_modificador}' aplicado ao jogador {jogador.nome}. Peso atual do voto: {peso_final}."
        },
    )

@router.post("/status-jogador")
async def alterar_status_jogador_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    id_jogador: str = Form(...),
    novo_status: str = Form(...),
    partida_id: str = Form("principal"),
):
    """Permite ao Storyteller alterar o status de vida / voto fantasma de um jogador."""
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode alterar o status de jogadores.")

    salas = _obter_salas_botc(request.app.state)
    sala = salas.get(partida_id, salas["principal"])
    sistema = sala["sistema"]

    try:
        status_enum = StatusJogador(novo_status)
        sistema.alterar_status_jogador(id_jogador, status_enum)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return templates.TemplateResponse(
        name="sucesso.html",
        request=request,
        context={"mensagem": f"Status do jogador {id_jogador} alterado para {novo_status}."},
    )

@router.post("/apurar")
async def apurar_execucao_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    partida_id: str = Form("principal"),
):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(
            status_code=403,
            detail="Apenas o Storyteller pode apurar a execução.",
        )

    salas = _obter_salas_botc(request.app.state)
    sala = salas.get(partida_id, salas["principal"])
    sistema = sala["sistema"]

    resultado = sistema.apurar_vencedor()
    # Ao encerrar o dia e apurar o executado, limpa os nomeados do dia para o próximo ciclo!
    sala.setdefault("nomeados_hoje", set()).clear()
    sala["giro"]["trancados"] = {}
    sala["giro"]["trancados_nomes"] = set()
    sala["giro"]["mensagem_final"] = ""

    mensagem = (
        f"O jogador executado foi: {resultado}"
        if resultado
        else "Ninguém foi executado. Empate ou votos insuficientes."
    )

    return templates.TemplateResponse(
        name="sucesso.html",
        request=request,
        context={"mensagem": mensagem},
    )
    
def _atualizar_progresso_giro(sala: dict) -> dict:
    """Atualiza o ponteiro do Storyteller no servidor (1.5s por jogador) e trava as mãos."""
    giro = sala["giro"]
    if not giro["ativo"]:
        return giro

    sistema = sala["sistema"]
    maos = sala["maos"]
    decorrido = time.time() - giro["inicio_ts"]
    passo_calculado = int(decorrido // 1.5)
    ordem = giro["ordem_ids"]

    for idx in range(min(passo_calculado, len(ordem))):
        jid = ordem[idx]
        if jid not in giro["trancados"]:
            jog = sistema.obter_jogador(jid)
            if jog:
                mao_no_momento = bool(maos.get(jog.nome, False) or maos.get(jog.id_jogador, False))
                giro["trancados"][jid] = mao_no_momento
                giro["trancados_nomes"].add(jog.nome)
                if mao_no_momento and jog.pode_votar():
                    giro["votos_computados"] += jog.calcular_peso_voto()
                    if jog.status == StatusJogador.MORTO_COM_FANTASMA:
                        jog.status = StatusJogador.MORTO_SEM_FANTASMA

    if passo_calculado >= len(ordem):
        giro["ativo"] = False
        giro["passo_atual"] = -1
        nome_alvo = giro["nomeado_nome"] or giro["nomeado_id"]
        try:
            sistema.registrar_votacao(nome_alvo, giro["votos_computados"])
        except ValueError:
            pass
        giro["mensagem_final"] = (
            f"Contagem concluída! {giro['votos_computados']} voto(s) computado(s) para {nome_alvo}."
        )
    else:
        giro["passo_atual"] = passo_calculado

    return giro

@router.post("/api/iniciar-giro")
async def iniciar_giro_storyteller(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    nomeado_id: str = Form(...),
    partida_id: str = Form("principal"),
):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode iniciar o ponteiro.")

    salas = _obter_salas_botc(request.app.state)
    sala = salas.get(partida_id, salas["principal"])
    sala.setdefault("nomeados_hoje", set())

    if sala["storyteller_id"] is None:
        sala["storyteller_id"] = usuario.id
        sala["storyteller_nome"] = usuario.nome_real or usuario.username
        sala["sistema"].jogadores.pop(usuario.id, None)
        sala["sistema"].jogadores.pop(usuario.username, None)
        sala["sistema"].jogadores.pop(usuario.nome_real, None)
    elif sala["storyteller_id"] != usuario.id:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller titular desta partida pode girar o ponteiro.")

    sistema = sala["sistema"]
    lista_jogadores = [j for j in sistema.jogadores.values() if j.id_jogador != sala["storyteller_id"]]
    if not lista_jogadores:
        raise HTTPException(status_code=400, detail="Não há jogadores votantes na roda.")

    idx_nomeado = next(
        (i for i, j in enumerate(lista_jogadores) if j.id_jogador == nomeado_id or j.nome == nomeado_id),
        0,
    )
    nomeado_obj = lista_jogadores[idx_nomeado]

    # Regra oficial do BoTC: um jogador só pode ser nomeado 1 vez por dia!
    if nomeado_obj.id_jogador in sala["nomeados_hoje"]:
        raise HTTPException(
            status_code=400,
            detail=f"{nomeado_obj.nome} já foi indicado(a) para a forca hoje! Escolha outro jogador ou encerre o dia.",
        )

    sala["nomeados_hoje"].add(nomeado_obj.id_jogador)

    # Ordem começa no jogador imediatamente à direita (sentido horário) e termina no próprio nomeado
    ordem_ids = [
        lista_jogadores[(idx_nomeado + offset) % len(lista_jogadores)].id_jogador
        for offset in range(1, len(lista_jogadores) + 1)
    ]

    sala["giro"] = {
        "ativo": True,
        "nomeado_id": nomeado_obj.id_jogador,
        "nomeado_nome": nomeado_obj.nome,
        "ordem_ids": ordem_ids,
        "inicio_ts": time.time(),
        "passo_atual": 0,
        "trancados": {},
        "trancados_nomes": set(),
        "votos_computados": 0,
        "mensagem_final": "",
    }
    return JSONResponse({"status": "iniciado", "nomeado": nomeado_obj.nome})

@router.get("/api/estado")
async def estado_roda_botc(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    partida_id: str = "principal",
):
    salas = _obter_salas_botc(request.app.state)
    sala = salas.get(partida_id, salas["principal"])
    sala.setdefault("nomeados_hoje", set())
    sala.setdefault("autorizados", set())
    sistema = sala["sistema"]

    # Verifica se a sala tem senha e se o usuário ainda não foi autorizado nela
    if sala.get("senha") and usuario.id not in sala["autorizados"] and sala["storyteller_id"] != usuario.id:
        return JSONResponse(
            {
                "requer_senha": True,
                "partida_atual": {"id": sala["id"], "nome": sala["nome"]},
                "partidas_disponiveis": [
                    {
                        "id": s["id"],
                        "nome": s["nome"],
                        "storyteller_nome": s["storyteller_nome"],
                        "tem_senha": bool(s.get("senha")),
                    }
                    for s in salas.values()
                ],
            },
            status_code=403,
        )

    sala["autorizados"].add(usuario.id)
    eh_st_desta_sala = _eh_storyteller_da_sala(sala, usuario)

    if eh_st_desta_sala:
        sistema.jogadores.pop(usuario.id, None)
        sistema.jogadores.pop(usuario.username, None)
        sistema.jogadores.pop(usuario.nome_real, None)

    jogador_atual = _obter_ou_criar_jogador(sistema, usuario, sala=sala)

    # Mocks apenas na sala principal! Novas salas começam limpas só com usuários reais.
    if partida_id == "principal" and len(sistema.jogadores) < 4:
        for nome in ["Alice", "Bruno", "Carla", "Diego", "Elena"]:
            if not sistema.obter_jogador(nome):
                sistema.adicionar_jogador(
                    JogadorBotC(id_jogador=nome.lower(), nome=nome, status=StatusJogador.VIVO)
                )

    giro = _atualizar_progresso_giro(sala)

    jogadores_roda = []
    for jog in sistema.jogadores.values():
        if jog.id_jogador == sala["storyteller_id"]:
            continue
        mao = sala["maos"].get(jog.nome, False) or sala["maos"].get(jog.id_jogador, False)
        trancado = jog.id_jogador in giro["trancados"]
        mao_exibida = giro["trancados"][jog.id_jogador] if trancado else bool(mao)
        jogadores_roda.append({
            "id": jog.id_jogador,
            "nome": jog.nome,
            "status": jog.status.value,
            "peso": jog.calcular_peso_voto(),
            "pode_votar": jog.pode_votar(),
            "mao_levantada": mao_exibida,
            "trancado": trancado,
            "ja_nomeado_hoje": jog.id_jogador in sala["nomeados_hoje"],
        })

    meu_trancado = bool(jogador_atual and jogador_atual.id_jogador in giro["trancados"])
    minha_mao = (
        giro["trancados"][jogador_atual.id_jogador]
        if (jogador_atual and meu_trancado)
        else bool(
            sala["maos"].get(usuario.username, False)
            or (jogador_atual and sala["maos"].get(jogador_atual.nome, False))
        )
    )

    id_ponteiro_atual = (
        giro["ordem_ids"][giro["passo_atual"]]
        if giro["ativo"] and 0 <= giro["passo_atual"] < len(giro["ordem_ids"])
        else None
    )

    return JSONResponse({
        "partida_atual": {
            "id": sala["id"],
            "nome": sala["nome"],
            "storyteller_id": sala["storyteller_id"],
            "storyteller_nome": sala["storyteller_nome"] or "Aguardando Storyteller",
        },
        "partidas_disponiveis": [
            {
                "id": s["id"],
                "nome": s["nome"],
                "storyteller_nome": s["storyteller_nome"],
                "tem_senha": bool(s.get("senha")),
            }
            for s in salas.values()
        ],
        "usuario_atual": {
            "username": usuario.username,
            "nome": usuario.username,
            "id": jogador_atual.id_jogador if jogador_atual else usuario.id,
            "status": "STORYTELLER (CENTRO DA RODA)" if eh_st_desta_sala else (jogador_atual.status.value if jogador_atual else "Vivo"),
            "pode_votar": False if eh_st_desta_sala else (jogador_atual.pode_votar() if jogador_atual else False),
            "mao_levantada": False if eh_st_desta_sala else minha_mao,
            "trancado": meu_trancado,
            "is_storyteller_desta_partida": eh_st_desta_sala,
            "tem_escopo_storyteller": "BOTC_STORYTELLER" in usuario.escopo,
        },
        "jogadores": jogadores_roda,
        "giro": {
            "ativo": giro["ativo"],
            "nomeado_id": giro["nomeado_id"],
            "nomeado_nome": giro["nomeado_nome"],
            "id_ponteiro_atual": id_ponteiro_atual,
            "votos_computados": giro["votos_computados"],
            "mensagem_final": giro["mensagem_final"],
        },
    })