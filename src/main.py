from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.australia import EleicaoAustralia
from src.autenticacao.australia import (
    EleitorAustralia,
)
from src.autenticacao.base import ServicoAutenticacao
from src.autenticacao.botc import JogadorBOTC
from src.autenticacao.caco import GestaoCACo
from src.botc import SistemaEleitoralBotC
from src.caco import EleicaoAssembleia
from src.database import carregar_estado_sql, inicializar_banco, salvar_estado_sql
from src.routers import australia_router, auth_router, botc_router, caco_router
from src.routers.dependencias import RequerRedirecionamentoException

app = FastAPI(title="Sistema de Votação Web")

@app.exception_handler(RequerRedirecionamentoException)
async def auth_exception_handler(request: Request, exc: RequerRedirecionamentoException):
    return RedirectResponse(url="/", status_code=302)

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent

# Configuração do Frontend com caminhos absolutos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="react_assets")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def _carregar_ou_inicializar(chave: str, valor_padrao: object) -> object:
    """Busca o estado no banco SQL; se ainda não existir, salva e retorna o padrão."""
    salvo = carregar_estado_sql(chave)
    if salvo is not None:
        return salvo
    salvar_estado_sql(chave, valor_padrao)
    return valor_padrao


inicializar_banco()

# --- INICIALIZAÇÃO DO BANCO DE AUTENTICAÇÃO ---
banco_auth_padrao = ServicoAutenticacao()
banco_auth_padrao.registrar(EleitorAustralia("caio", "senha123", "Caio Lima"))
banco_auth_padrao.registrar(GestaoCACo("julia", "admin", "Julia Nardo"))
banco_auth_padrao.registrar(JogadorBOTC("leo", "botc123", "Leonardo Carvalho"))

app.state.banco_auth = _carregar_ou_inicializar("banco_auth", banco_auth_padrao)

# --- INICIALIZAÇÃO DA ELEIÇÃO DA AUSTRÁLIA ---
CANDIDATOS_AUSTRALIA = ["Candidato A", "Candidato B", "Candidato C"]
PARTIDOS_AUSTRALIA = {
    "Partido Azul": ["Candidato A"],
    "Partido Verde": ["Candidato B"],
    "Partido Amarelo": ["Candidato C"],
}
eleicao_australia_padrao = EleicaoAustralia(
    candidatos_ids=CANDIDATOS_AUSTRALIA,
    cedulas=[],
    partidos_candidatos=PARTIDOS_AUSTRALIA,
)
app.state.eleicao_australia = _carregar_ou_inicializar("eleicao_australia", eleicao_australia_padrao)
app.state.eleitores_australia_votaram = _carregar_ou_inicializar("eleitores_australia_votaram", set())

# --- INICIALIZAÇÃO DA ASSEMBLEIA DO CACO ---
alunos_caco = [app.state.banco_auth._mapa_usernames["julia"]]
eleicao_caco_padrao = EleicaoAssembleia(
    alunos_cadastrados_ids=alunos_caco,
    eleitores_ids=alunos_caco,
    duracao_ciclo=60,
)
app.state.eleicao_caco = _carregar_ou_inicializar("eleicao_caco", eleicao_caco_padrao)
app.state.eleitores_caco_votaram = _carregar_ou_inicializar("eleitores_caco_votaram", set())

# --- INICIALIZAÇÃO DA PARTIDA DO BOTC ---
sistema_botc_padrao = SistemaEleitoralBotC(jogadores_vivos=10)
app.state.sistema_botc = _carregar_ou_inicializar("sistema_botc", sistema_botc_padrao)
app.state.maos_botc = _carregar_ou_inicializar("maos_botc", {})
app.state.salas_botc = _carregar_ou_inicializar("salas_botc", {})
app.state._salas_botc_iniciadas = bool(app.state.salas_botc)

# Registro dos controladores
app.include_router(auth_router.router)
app.include_router(australia_router.router)
app.include_router(botc_router.router)
app.include_router(caco_router.router)

@app.middleware("http")
async def servir_spa_react_em_producao(request: Request, call_next):
    """Serve o frontend React em produção no Render quando o navegador pede uma página HTML.
    """
    is_test_client = request.headers.get("user-agent", "").startswith("testclient")
    path = request.url.path
    accept = request.headers.get("accept", "")
    pede_json = "application/json" in accept and "text/html" not in accept

    rotas_backend = (
        "/api",
        "/botc/api",
        "/australia/api",
        "/caco/api",
        "/static",
        "/assets",
        "/logout",
    )
    
    if (
        not is_test_client
        and request.method == "GET"
        and not pede_json
        and not path.startswith(rotas_backend)
        and (FRONTEND_DIST / "index.html").exists()
    ):
        return FileResponse(
            FRONTEND_DIST / "index.html",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )

    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Redireciona a raiz direto para o login
    return templates.TemplateResponse(request=request, name="login.html", context={})