from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.routers import auth_router, australia_router, caco_router, botc_router
from src.autenticacao.base import ServicoAutenticacao
from src.autenticacao.caco import GestaoCACo
from src.autenticacao.australia import EleitorAustralia

app = FastAPI(title="Sistema de Votação Web")

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent

# Configuração do Frontend com caminhos absolutos
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Banco de Dados em Memória
banco_auth = ServicoAutenticacao()
# Usuários pré-cadastrados para teste <- Talvez seja melhor mudar depois
banco_auth.registrar(EleitorAustralia("caio", "senha123", "Caio Lima"))
banco_auth.registrar(GestaoCACo("julia", "admin", "Julia Nardo", "281272"))

# Injeta o banco nas rotas
app.state.banco_auth = banco_auth

# Registro dos controladores
app.include_router(auth_router.router)
app.include_router(australia_router.router)
app.include_router(botc_router.router)
app.include_router(caco_router.router)

@app.get("/")
async def root(request: Request):
    # Redireciona a raiz direto para o login
    return templates.TemplateResponse("login.html", {"request": request})