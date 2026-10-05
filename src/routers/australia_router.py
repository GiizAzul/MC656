from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .dependencias import obter_usuario_logado

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent

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
async def processar_voto(request: Request, ranking: str = Form(...)):
    # Aqui entra a lógica de converter a string que vem do form HTML 
    # (ex: "A,C,B") em uma lista e injetar na classe EleicaoAustralia.
    # Por enquanto, apenas redirecionamos para uma tela de sucesso.
    return templates.TemplateResponse(
        name="sucesso.html", 
        request=request, 
        context={"mensagem": "Voto registrado com sucesso na Eleição Federal!"}
    )