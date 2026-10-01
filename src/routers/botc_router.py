from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/botc", tags=["BOTC"])
templates = Jinja2Templates(directory="templates")

# Memória interna de jogadores para a roda visual
JOGADORES_MOCK = [
    {"nome": "Leo", "status": "Vivo"},
    {"nome": "Julia", "status": "Morto (Sem Voto)"},
    {"nome": "Caio", "status": "Vivo"}
]

@router.get("/partida", response_class=HTMLResponse)
async def tela_partida(request: Request):
    usuario_logado = request.cookies.get("sessao_usuario")
    if not usuario_logado:
        return RedirectResponse(url="/")
        
    return templates.TemplateResponse(
        "botc.html", 
        {"request": request, "jogadores": JOGADORES_MOCK}
    )

@router.post("/votar")
async def processar_voto_botc(request: Request, acao: str = Form(...)):
    # acao receberá "levantar_mao" ou "abaixar_mao"
    return templates.TemplateResponse(
        "sucesso.html", 
        {"request": request, "mensagem": "Ação registrada na roda da cidade."}
    )