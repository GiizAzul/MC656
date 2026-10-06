from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .dependencias import obter_usuario_logado
from src.autenticacao.base import Usuario

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/australia", tags=["Australia"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Simulação de uma eleição ativa em memória
CANDIDATOS_MOCK = ["Candidato A", "Candidato B", "Candidato C"]

@router.get("/votar", response_class=HTMLResponse)
async def tela_votacao(request: Request):
    usuario_logado = await obter_usuario_logado(request)
    if not usuario_logado:
        return RedirectResponse(url="/")
        
    return templates.TemplateResponse(
        name="australia.html", 
        request=request,
        context={"candidatos": CANDIDATOS_MOCK}
    )

@router.post("/votar")
async def processar_voto(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    if "AUSTRALIA" not in usuario.escopo:
        # Redirect para a raiz em caso de fraude de escopo:
        return RedirectResponse(url="/", status_code=302)
        
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
        # Recupera a eleição do estado global
        eleicao = request.app.state.eleicao_australia 
        
        # ATENÇÃO: Dependendo de como sua classe de domínio foi feita, adicione a cédula:
        # Exemplo 1: eleicao.registrar_voto(cedula_ordenada)
        # Exemplo 2: eleicao.cedulas.append(cedula_ordenada)
        eleicao.cedulas.append(cedula_ordenada) # <--- Adapte para o método real da sua classe
        
        return templates.TemplateResponse(
            request=request, 
            name="sucesso.html", 
            context={"mensagem": "Voto registrado com sucesso na Eleição Federal!"}
        )
    except ValueError as e:
        return templates.TemplateResponse(
            request=request, 
            name="australia.html", 
            context={"candidatos": list(eleicao.candidatos.keys()), "erro": str(e)}
        )