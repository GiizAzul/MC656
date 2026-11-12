from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
async def tela_partida(request: Request, usuario: Annotated[Usuario, Depends(obter_usuario_logado)]):
    if "BOTC" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    sistema = request.app.state.sistema_botc
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
        },
    )


@router.post("/votar")
async def processar_voto_botc(
    request: Request,
    acao: str = Form(...),
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)] = None,
):
    sistema = request.app.state.sistema_botc
    if usuario is not None and "BOTC" in usuario.escopo:
        jogador = _obter_ou_criar_jogador(sistema, usuario)
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
                    "erro": "Você está morto e não possui mais voto fantasma para votar nesta partida.",
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
    """Permite ao Storyteller alterar o status de vida / voto fantasma de um jogador (Issue #71)."""
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
async def apurar_execucao_botc(request: Request, usuario: Annotated[Usuario, Depends(obter_usuario_logado)]):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode apurar a execução.")

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
