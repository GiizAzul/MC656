from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.caco import OpcaoVoto
from src.autenticacao.base import Usuario

from .dependencias import obter_usuario_logado

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/caco", tags=["CACo"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.post("/iniciar")
async def iniciar_votacao_caco(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    if "CACO_GESTAO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_caco

    try:
        eleicao.iniciar_votacao()
        
        return templates.TemplateResponse(
            request=request,
            name="sucesso.html",
            context={"mensagem": "Votação da Assembleia iniciada com sucesso!"}
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": str(e),
                "estado_eleicao": eleicao.estado.name,
                "is_gestao": True
            }
        )

@router.get("/assembleia", response_class=HTMLResponse)
async def tela_assembleia(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    if "CACO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)
        
    eleicao = request.app.state.eleicao_caco
    is_gestao = "GESTAO" in usuario.escopo
        
    return templates.TemplateResponse(
        name="caco.html", 
        request=request,
        context={
            "estado_eleicao": eleicao.estado.name,
            "is_gestao": is_gestao
        }
    )
    
@router.post("/votar")
async def processar_voto_caco(request: Request, opcao: str = Form(...), usuario: Usuario = Depends(obter_usuario_logado)):
    if "CACO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    # Puxa o contexto global de eleição
    eleicao = request.app.state.eleicao_caco

    # Bloqueia se o usuário já votou
    if usuario.id in request.app.state.eleitores_caco_votaram:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": "VOTO NEGADO: Você já registrou seu voto nesta pauta.",
                "estado_eleicao": eleicao.estado.name,
                "is_gestao": "GESTAO" in usuario.escopo
            }
        )

    try:
        opcao_enum = OpcaoVoto[opcao]
        
        eleicao.registrar_voto(usuario.id, opcao_enum)
        
        # Assina a lista de presença marcando que o ID já votou
        request.app.state.eleitores_caco_votaram.add(usuario.id)
        
        return templates.TemplateResponse(
            request=request, 
            name="sucesso.html", 
            context={"mensagem": f"Seu voto na assembleia foi contabilizado como: {opcao}"}
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": str(e),
                "estado_eleicao": eleicao.estado.name,
                "is_gestao": "GESTAO" in usuario.escopo
            }
        )

@router.post("/encerrar")
async def encerrar_votacao_caco(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    if "CACO_GESTAO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_caco

    try:
        # Garante que a votação será fechada
        eleicao.encerrar_votacao()
        
        return templates.TemplateResponse(
            request=request,
            name="sucesso.html",
            context={"mensagem": "Votação da Assembleia encerrada."}
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": str(e),
                "estado_eleicao": eleicao.estado.name,
                "is_gestao": True
            }
        )

@router.get("/resultados", response_class=HTMLResponse)
async def resultados_caco(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Acesso negado.")   # Tem que ver issae
    eleicao = request.app.state.eleicao_caco
    
    contadores = eleicao.obter_contadores()
    
    # Calcula o total para fazer as barras de porcentagem no HTML
    total_votos = sum(contadores.values())
    
    return templates.TemplateResponse(
        name="resultados_caco.html",
        request=request, 
        context={
            "contadores": contadores,
            "total_votos": total_votos,
            "estado": eleicao.estado.name
        }
    )