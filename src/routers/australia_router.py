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

@router.get("/votar", response_class=HTMLResponse)
async def tela_votacao(request: Request, usuario: Annotated[Usuario, Depends(obter_usuario_logado)]):
    # Valida apenas a permissão da pauta, pois o Depends já garantiu o login
    if "AUSTRALIA" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_australia
    candidatos_reais = list(eleicao.candidatos)
    
    return templates.TemplateResponse(
        name="australia.html", 
        request=request,
        context={"candidatos": candidatos_reais}
    )    

@router.post("/votar")
async def processar_voto_australia(request: Request, usuario: Annotated [Usuario, Depends(obter_usuario_logado)]):
    if "AUSTRALIA" not in usuario.escopo:
        # Redirect para a raiz em caso de fraude de escopo:
        return RedirectResponse(url="/", status_code=302)
        
    # Recupera a eleição do estado global
    eleicao = request.app.state.eleicao_australia 
    candidatos_reais = list(eleicao.candidatos.keys()) if isinstance(eleicao.candidatos, dict) else eleicao.candidatos

    # Verifica se o usuário logado já votou
    if usuario.id in request.app.state.eleitores_australia_votaram:
        return templates.TemplateResponse(
            request=request, 
            name="australia.html", 
            context={
                "candidatos": candidatos_reais, 
                "erro": "Você já registrou seu voto nesta eleição."
            }
        )

    form_data = await request.form()
    
    # Coleta e ordena os candidatos com base nos números digitados
    tuplas_posicao = []
    for chave, valor in form_data.items():
        if chave.startswith("posicao_") and valor.strip().isdigit():
            nome_candidato = chave.replace("posicao_", "")
            tuplas_posicao.append((int(valor), nome_candidato))
            
    # Ordena a lista pela nota (1, 2, 3...)
    tuplas_posicao.sort(key=lambda x: x[0])
    cedula_ordenada = [candidato for posicao, candidato in tuplas_posicao]
    
    try:
        # O usuário não pode pular candidatos
        if len(cedula_ordenada) != len(eleicao.candidatos):
            raise ValueError(f"Erro: Você ranqueou {len(cedula_ordenada)} candidatos. Você deve ranquear exatamente todos os {len(candidatos_reais)} candidatos.")

        posicoes_originais = [pos for pos, cand in tuplas_posicao]
        posicoes_esperadas = list(range(1, len(candidatos_reais) + 1))

        if sorted(posicoes_originais) != posicoes_esperadas:
                    raise ValueError("As posições informadas são inválidas. Não é permitido repetir números ou pular posições.\nInsira um número diferente para cada candidato.")
        
        # Deposita a cédula na urna
        eleicao.cedulas.append(cedula_ordenada) 

        # Marca que este usuário já votou
        request.app.state.eleitores_australia_votaram.add(usuario.id)
        
        return templates.TemplateResponse(
            request=request, 
            name="sucesso.html", 
            context={"mensagem": "Voto registrado com sucesso na Eleição Federal!"}
        )
    except ValueError as e:
        return templates.TemplateResponse(
            request=request, 
            name="australia.html",  
            context={
                "candidatos": candidatos_reais, 
                "erro": str(e)
            }
        )
