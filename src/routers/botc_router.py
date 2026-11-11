from pathlib import Path
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.autenticacao.base import Usuario
from src.botc import (
    JogadorBotC,
    StatusJogador,
)

from .dependencias import obter_usuario_logado

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/botc", tags=["BOTC"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _obter_ou_criar_jogador(sistema, usuario: Usuario) -> JogadorBotC:
    """Garante que o usuário autenticado esteja registrado no sistema eleitoral BotC."""
    jogador = (
        sistema.obter_jogador(usuario.id)
        or sistema.obter_jogador(usuario.username)
        or sistema.obter_jogador(usuario.nome_real)
    )
    if not jogador:
        jogador = JogadorBotC(
            id_jogador=usuario.id,
            nome=usuario.nome_real or usuario.username,
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

    sistema = request.app.state.sistema_botc
    maos = getattr(request.app.state, "maos_botc", {})
    mao_levantada = maos.get(usuario.username, False)
    
    jogador_atual = _obter_ou_criar_jogador(sistema, usuario)

    jogadores_view = []
    for jog in sistema.jogadores.values():
        jogadores_view.append({
            "id": jog.id_jogador,
            "nome": jog.nome,
            "status": jog.status.value,
            "peso": jog.calcular_peso_voto(),
        })

    is_storyteller = "STORYTELLER" in usuario.escopo

    return templates.TemplateResponse(
        name="botc.html",
        request=request,
        context={
            "jogadores": jogadores_view,
            "votos": getattr(sistema, "votos", {}),
            "is_storyteller": is_storyteller,
            "pode_votar": jogador_atual.pode_votar(),
            "status_usuario": jogador_atual.status.value,
            "mao_levantada": mao_levantada,
            "maos_ativas": maos,
        },
    )


@router.post("/votar")
async def processar_voto_botc(
    request: Request,
    acao: str = Form(...),
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)] = None,
):
    if not hasattr(request.app.state, "maos_botc"):
        request.app.state.maos_botc = {}

    giro = getattr(request.app.state, "giro_botc", None)
    if giro and giro.get("ativo") and usuario is not None:
        if usuario.id in giro.get("trancados", {}) or usuario.nome_real in giro.get("trancados_nomes", set()):
            if "application/json" in request.headers.get("accept", ""):
                return JSONResponse(
                    {"erro": "O ponteiro já passou por você! Seu voto foi computado e sua mão está travada."},
                    status_code=400,
                )
    
    mao_levantada = acao == "levantar_mao"
    
    sistema = request.app.state.sistema_botc

    if usuario is not None and "BOTC" in usuario.escopo:
        request.app.state.maos_botc[usuario.username] = mao_levantada
        request.app.state.maos_botc[usuario.id] = mao_levantada
        jogador = _obter_ou_criar_jogador(sistema, usuario)
        # Se a requisição vier via fetch/React (Accept: application/json), responde sem trocar de tela!
        if "application/json" in request.headers.get("accept", ""):
            total_maos = sum(1 for v in request.app.state.maos_botc.values() if v)
            return JSONResponse({
                "status": "ok",
                "mao_levantada": mao_levantada,
                "total_maos": total_maos,
                "mensagem": "Ação registrada na roda da cidade.",
            })
        if not jogador.pode_votar():
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
    """Permite ao Storyteller configurar modificadores ocultos em jogadores (Issue #70)."""
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
):
    """Permite ao Storyteller alterar o status de vida / voto fantasma de um jogador"""
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode alterar o status de jogadores.")

    sistema = request.app.state.sistema_botc
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
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)]
):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(
            status_code=403, 
            detail="Apenas o Storyteller pode apurar a execução."
        )

    resultado = request.app.state.sistema_botc.apurar_vencedor()

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

def _atualizar_progresso_giro(app_state, sistema) -> dict:
    """Atualiza o ponteiro do Storyteller no servidor (1.5s por jogador) e trava as mãos."""
    if not hasattr(app_state, "giro_botc"):
        app_state.giro_botc = {
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
        }

    giro = app_state.giro_botc
    if not giro["ativo"]:
        return giro

    decorrido = time.time() - giro["inicio_ts"]
    passo_calculado = int(decorrido // 1.5)  # 1.5 segundo em cada jogador (fluido e visível)
    ordem = giro["ordem_ids"]
    maos = getattr(app_state, "maos_botc", {})

    # Trava todos os jogadores pelos quais o ponteiro já passou
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
):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode iniciar o ponteiro.")

    sistema = request.app.state.sistema_botc
    lista_jogadores = list(sistema.jogadores.values())
    if not lista_jogadores:
        raise HTTPException(status_code=400, detail="Não há jogadores na roda.")

    idx_nomeado = next(
        (i for i, j in enumerate(lista_jogadores) if j.id_jogador == nomeado_id or j.nome == nomeado_id),
        0,
    )
    nomeado_obj = lista_jogadores[idx_nomeado]

    # Ordem começa no jogador imediatamente à direita (sentido horário) e termina no próprio nomeado
    ordem_ids = [
        lista_jogadores[(idx_nomeado + offset) % len(lista_jogadores)].id_jogador
        for offset in range(1, len(lista_jogadores) + 1)
    ]

    request.app.state.giro_botc = {
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
):
    sistema = request.app.state.sistema_botc
    if not hasattr(request.app.state, "maos_botc"):
        request.app.state.maos_botc = {}

    _obter_ou_criar_jogador(sistema, usuario)

    nomes_demo = ["Alice", "Bruno", "Carla", "Diego", "Elena"]
    if len(sistema.jogadores) < 4:
        for nome in nomes_demo:
            if not sistema.obter_jogador(nome):
                sistema.adicionar_jogador(
                    JogadorBotC(id_jogador=nome.lower(), nome=nome, status=StatusJogador.VIVO)
                )

    giro = _atualizar_progresso_giro(request.app.state, sistema)

    jogadores_roda = []
    for jog in sistema.jogadores.values():
        mao = request.app.state.maos_botc.get(jog.nome, False) or request.app.state.maos_botc.get(jog.id_jogador, False)
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
        })

    jogador_atual = _obter_ou_criar_jogador(sistema, usuario)
    meu_trancado = jogador_atual.id_jogador in giro["trancados"]
    minha_mao = (
        giro["trancados"][jogador_atual.id_jogador]
        if meu_trancado
        else bool(
            request.app.state.maos_botc.get(usuario.username, False)
            or request.app.state.maos_botc.get(jogador_atual.nome, False)
        )
    )

    id_ponteiro_atual = (
        giro["ordem_ids"][giro["passo_atual"]]
        if giro["ativo"] and 0 <= giro["passo_atual"] < len(giro["ordem_ids"])
        else None
    )

    return JSONResponse({
        "usuario_atual": {
            "username": usuario.username,
            "nome": jogador_atual.nome,
            "id": jogador_atual.id_jogador,
            "status": jogador_atual.status.value,
            "pode_votar": jogador_atual.pode_votar(),
            "mao_levantada": minha_mao,
            "trancado": meu_trancado,
            "is_storyteller": "STORYTELLER" in usuario.escopo,
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