from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.caco import OpcaoVoto

from .dependencias import obter_usuario_logado

router = APIRouter(prefix="/caco", tags=["CACo"])
templates = Jinja2Templates(directory="templates")

@router.get("/assembleia", response_class=HTMLResponse)
async def tela_assembleia(request: Request):
    usuario_logado = await obter_usuario_logado(request)
    if not usuario_logado:
        return RedirectResponse(url="/")
        
    return templates.TemplateResponse("caco.html", {"request": request})

@router.post("/votar")
async def processar_voto_caco(request: Request, opcao: str = Form(...)):
    # opcao receberá "APROVAR", "REJEITAR" ou "ABSTER" do HTML
    return templates.TemplateResponse(
        "sucesso.html", 
        {"request": request, "mensagem": "Seu voto na assembleia foi contabilizado."}
    )