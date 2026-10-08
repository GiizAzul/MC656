from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.autenticacao.base import Usuario

from .dependencias import obter_usuario_logado

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/botc", tags=["BOTC"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Memória interna de jogadores para a roda visual
JOGADORES_MOCK = [
    {"nome": "Leo", "status": "Vivo"},
    {"nome": "Julia", "status": "Morto (Sem Voto)"},
    {"nome": "Caio", "status": "Vivo"}
]

@router.get("/partida", response_class=HTMLResponse)
async def tela_partida(request: Request):
    usuario_logado = await obter_usuario_logado(request)
    if not usuario_logado or "BOTC" not in usuario_logado.escopo:
        return RedirectResponse(url="/")
        
    sistema = request.app.state.sistema_botc
    
    # O HTML do botc exige essas variáveis para renderizar a roda de jogadores
    # e verificar se o usuário atual é o Storyteller.
    return templates.TemplateResponse(
        name="botc.html", 
        request=request,
        context={
            "jogadores": [],
            "votos": sistema.votos if hasattr(sistema, 'votos') else {},
            "is_storyteller": "STORYTELLER" in usuario_logado.escopo
        }
    )

@router.post("/votar")
async def processar_voto_botc(request: Request, acao: str = Form(...)):
    # acao receberá "levantar_mao" ou "abaixar_mao"
    return templates.TemplateResponse(
        name="sucesso.html", 
        request=request, 
        context={"mensagem": "Ação registrada na roda da cidade."}
    )

@router.post("/registrar")
async def registrar_votos_botc(
    request: Request, 
    nomeado: str = Form(...), 
    num_votos: int = Form(...),
    usuario: Usuario = Depends(obter_usuario_logado)
):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode registrar votos.")

    # request.app.state.sistema_botc.registrar_votacao(nomeado, num_votos)
    
    return templates.TemplateResponse(
        name="sucesso.html", 
        request=request, 
        context={"mensagem": f"{num_votos} votos registrados para {nomeado}."}
    )

@router.post("/apurar")
async def apurar_execucao_botc(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    if "BOTC_STORYTELLER" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas o Storyteller pode apurar a execução.")

    # resultado = request.app.state.sistema_botc.apurar_vencedor()
    # Mock temporário
    resultado = "Jogador X" 
    
    mensagem = f"O jogador executado foi: {resultado}" if resultado else "Ninguém foi executado. Empate ou votos insuficientes."

    return templates.TemplateResponse(
        name="sucesso.html", 
        request=request, 
        context={"mensagem": mensagem}
    )