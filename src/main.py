from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.routers import auth_router, australia_router, caco_router, botc_router
from src.routers.dependencias import RequerRedirecionamentoException

from src.autenticacao.base import ServicoAutenticacao
from src.autenticacao.caco import GestaoCACo
from src.autenticacao.australia import EleitorAustralia
from src.autenticacao.botc import JogadorBOTC

from src.australia import EleicaoAustralia
from src.caco import EleicaoAssembleia
from src.botc import SistemaEleitoralBotC

app = FastAPI(title="Sistema de Votação Web")

@app.exception_handler(RequerRedirecionamentoException)
async def auth_exception_handler(request: Request, exc: RequerRedirecionamentoException):
    return RedirectResponse(url="/", status_code=302)

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent

# Configuração do Frontend com caminhos absolutos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- INICIALIZAÇÃO DO BANCO EM MEMÓRIA ---
banco_auth = ServicoAutenticacao()
# Usuários pré-cadastrados para teste <- Talvez seja melhor mudar depois
banco_auth.registrar(EleitorAustralia("caio", "senha123", "Caio Lima"))
banco_auth.registrar(GestaoCACo("julia", "admin", "Julia Nardo"))
banco_auth.registrar(JogadorBOTC("leo", "botc123", "Leonardo Carvalho"))

# Injeta o banco nas rotas
app.state.banco_auth = banco_auth


# Inicialização das eleições
# Cria a eleição da Austrália com os candidatos
CANDIDATOS_AUSTRALIA = ["Candidato A", "Candidato B", "Candidato C"]
eleicao_australia = EleicaoAustralia(candidatos=CANDIDATOS_AUSTRALIA, cedulas=[])
app.state.eleicao_australia = eleicao_australia

# Cria a assembleia do CACo
alunos_caco = [banco_auth._mapa_usernames["julia"]] # IDs dos alunos habilitados
eleicao_caco = EleicaoAssembleia(alunos_cadastrados=alunos_caco, eleitores=alunos_caco, duracao_ciclo=60)
app.state.eleicao_caco = eleicao_caco

# Cria a partida do BoTC
sistema_botc = SistemaEleitoralBotC(jogadores_vivos=10)
app.state.sistema_botc = sistema_botc

# Registro dos controladores
app.include_router(auth_router.router)
app.include_router(australia_router.router)
app.include_router(botc_router.router)
app.include_router(caco_router.router)

@app.get("/")
async def root(request: Request):
    # Redireciona a raiz direto para o login
    return templates.TemplateResponse(request=request, name="login.html", context={})