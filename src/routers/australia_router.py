from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.autenticacao.base import Usuario

from .dependencias import obter_usuario_logado

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/australia", tags=["Australia"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def _contexto_cedula(eleicao, usuario: Usuario, **extra) -> dict:
    """Contexto padrão de australia.html: toda resposta que renderiza o template deve usá-lo,
    pois a tela depende de `estado_eleicao` para decidir se mostra a cédula."""
    return {
        "candidatos": list(eleicao.candidatos),
        "estado_eleicao": eleicao.estado.nome,
        "is_gestao": "AUSTRALIA_GESTAO" in usuario.escopo,
        **extra,
    }

@router.get("/votar", response_class=HTMLResponse)
async def tela_votacao(
    request: Request, 
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)]
):
    # Valida apenas a permissão da pauta, pois o Depends já garantiu o login
    if "AUSTRALIA" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_australia
    
    # Apenas exibe a tela; o template decide o que mostrar conforme o estado da eleição
    return templates.TemplateResponse(
        name="australia.html",
        request=request,
        context=_contexto_cedula(eleicao, usuario),
    )


@router.post("/iniciar")
async def iniciar_votacao_australia(request: Request, usuario: Annotated[Usuario, Depends(obter_usuario_logado)]):
    if "AUSTRALIA_GESTAO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_australia

    try:
        eleicao.iniciar_votacao()
    except RuntimeError as e:
        return templates.TemplateResponse(
            request=request,
            name="australia.html",
            context=_contexto_cedula(eleicao, usuario, erro=str(e)),
        )

    return templates.TemplateResponse(
        request=request,
        name="sucesso.html",
        context={"mensagem": "Eleição iniciada com sucesso!"},
    )


@router.post("/encerrar")
async def encerrar_votacao_australia(request: Request, usuario: Annotated[Usuario, Depends(obter_usuario_logado)]):
    if "AUSTRALIA_GESTAO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_australia

    try:
        eleicao.encerrar_votacao()
    except RuntimeError as e:
        return templates.TemplateResponse(
            request=request,
            name="australia.html",
            context=_contexto_cedula(eleicao, usuario, erro=str(e)),
        )

    return templates.TemplateResponse(
        request=request,
        name="sucesso.html",
        context={"mensagem": "Eleição encerrada."},
    )


@router.post("/votar")
async def processar_voto_australia(
    request: Request, 
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)]
):
    if "AUSTRALIA" not in usuario.escopo:
        # Redirect para a raiz em caso de fraude de escopo:
        return RedirectResponse(url="/", status_code=302)

    # Recupera a eleição do estado global
    eleicao = request.app.state.eleicao_australia
    candidatos_reais = list(eleicao.candidatos)


    # Verifica se o usuário logado já votou
    if usuario.id in request.app.state.eleitores_australia_votaram:
        return templates.TemplateResponse(
            request=request,
            name="australia.html",
            context=_contexto_cedula(eleicao, usuario, erro="Você já registrou seu voto nesta eleição."),
        )

    form_data = await request.form()

    try:
        # Traduz o formulário (posicao_<candidato> = número) em uma lista ordenada de candidatos
        tuplas_posicao = []
        for chave, valor in form_data.items():
            if chave.startswith("posicao_"):
                valor_limpo = str(valor).strip()
                if not valor_limpo:
                    continue
                if not valor_limpo.isdigit():
                    raise ValueError(
                        "Erro: As posições informadas são inválidas. Insira apenas números inteiros positivos (sem casas decimais ou sinais)."   
                    )
                nome_candidato = chave.replace("posicao_", "", 1)
                tuplas_posicao.append((int(valor_limpo), nome_candidato))

        # Ordena a lista pela nota (1, 2, 3...)
        tuplas_posicao.sort(key=lambda x: x[0])
        cedula_ordenada = [candidato for _, candidato in tuplas_posicao]

        if len(cedula_ordenada) != len(eleicao.candidatos):
            raise ValueError(
                f"Erro: Você ranqueou {len(cedula_ordenada)} candidatos. Você deve ranquear exatamente todos os {len(candidatos_reais)} candidatos."
            )

        # Os números digitados devem ser 1..N sem repetir nem pular posições
        posicoes_originais = [pos for pos, _ in tuplas_posicao]
        posicoes_esperadas = list(range(1, len(candidatos_reais) + 1))

        if sorted(posicoes_originais) != posicoes_esperadas:
            raise ValueError(
                "As posições informadas são inválidas. Não é permitido repetir números ou pular posições.\nInsira um número diferente para cada candidato."
            )

        # O motor valida a cédula (todos os candidatos, sem duplicatas) e respeita o estado da votação
        eleicao.apurar_voto(usuario.id, cedula_ordenada)

        # Marca que este usuário já votou
        request.app.state.eleitores_australia_votaram.add(usuario.id)

        return templates.TemplateResponse(
            request=request,
            name="sucesso.html",
            context={"mensagem": "Voto registrado com sucesso na Eleição Federal!"},
        )
    except (RuntimeError, ValueError) as e:
        return templates.TemplateResponse(
            request=request,
            name="australia.html",
            context=_contexto_cedula(eleicao, usuario, erro=str(e)),
        )

@router.get("/api/estado")
async def estado_australia_json(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
):
    from fastapi.responses import JSONResponse

    eleicao = request.app.state.eleicao_australia
    return JSONResponse({
        "candidatos": list(eleicao.candidatos),
        "estado_eleicao": eleicao.estado.nome,
        "is_gestao": "AUSTRALIA_GESTAO" in usuario.escopo,
        "ja_votou": usuario.id in request.app.state.eleitores_australia_votaram,
        "total_votos": len(eleicao.cedulas),
    })