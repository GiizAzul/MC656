from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.autenticacao.base import Usuario
from src.autenticacao.australia import CandidatoAustralia, EleitorAustralia
from src.autenticacao.botc import JogadorBOTC, StoryTellerBOTC
from src.autenticacao.caco import EstudanteCACo, GestaoCACo

from .dependencias import obter_usuario_logado

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/admin", response_class=HTMLResponse)
async def painel_admin(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    # Impede que usuários comuns entrem na tela de gestão
    if "GESTAO" not in usuario.escopo and "STORYTELLER" not in usuario.escopo:
        return RedirectResponse(url="/dashboard")
        
    return templates.TemplateResponse(request=request, name="admin.html", context={"usuario": usuario})

@router.get("/cadastro", response_class=HTMLResponse)
async def tela_cadastro(request: Request):
    return templates.TemplateResponse(request=request, name="cadastro.html", context={})

@router.post("/cadastro")
async def processar_cadastro(
    request: Request,
    tipo_conta: str = Form(...),
    username: str = Form(...),
    senha: str = Form(...),
    senha_confirma: str = Form(...),
    nome_real: str = Form(...),
    ra: str = Form(None) # Opcional no form, obrigatório para EstudanteCACo
):
    try:
        if senha != senha_confirma: # Verifica se as senhas inseridas batem
            raise ValueError("Senhas não conferem. Tente novamente")
        banco = request.app.state.banco_auth
    
        # Análise condicional do tipo de usuário
        if tipo_conta == "CACO_ESTUDANTE":
            if not ra or not ra.isnumeric():
                raise ValueError("RA inválido. Tente novamente.")
            novo_usuario = EstudanteCACo(username, senha, nome_real, int(ra))
        elif tipo_conta == "CACO_GESTAO":
            novo_usuario = GestaoCACo(username, senha, nome_real)
        elif tipo_conta == "AUSTRALIA_ELEITOR":
            novo_usuario = EleitorAustralia(username, senha, nome_real)
        elif tipo_conta == "AUSTRALIA_CANDIDATO":
            novo_usuario = CandidatoAustralia(username, senha, nome_real)
        elif tipo_conta == "BOTC_JOGADOR":
            novo_usuario = JogadorBOTC(username, senha, nome_real)
        elif tipo_conta == "BOTC_STORYTELLER":
            novo_usuario = StoryTellerBOTC(username, senha, nome_real)
        else:
            raise ValueError("Tipo de conta desconhecido.")
            
        banco.registrar(novo_usuario)

        # Adiciona alunos e gestores novos na lista de eleitores da assembleia ativa 
        if tipo_conta in ("CACO_ESTUDANTE", "CACO_GESTAO"):
            eleicao_caco = request.app.state.eleicao_caco
            eleicao_caco.alunos_cadastrados.add(novo_usuario.id)
            eleicao_caco.eleitores.add(novo_usuario.id)
        
        # return RedirectResponse(url="/", status_code=302)
        
        # Faz o login automático após cadastro
        resposta = RedirectResponse(url="/dashboard", status_code=302)
        resposta.set_cookie(key="sessao_usuario", value=username, httponly=True)
        return resposta
        
    except ValueError as erro:
        # Devolve o HTML de erro preenchendo os dados antigos para não apagar a tela
        return templates.TemplateResponse(
            request=request,
            name="cadastro.html",
            context={
                "erro": str(erro),
                "tipo_conta_selecionada": tipo_conta,
                "nome_real_digitado": nome_real,
                "username_digitado": username,
                "ra_digitado": ra
            }
        )

@router.post("/login")
async def processar_login(
    request: Request, 
    username: str = Form(...), 
    senha: str = Form(...)
):
    banco = request.app.state.banco_auth
    try:
        usuario = banco.login(username, senha)
        
        # Redireciona para o painel principal após sucesso
        resposta = RedirectResponse(url="/dashboard", status_code=302)
        
        # Salva o ID/Username no Cookie do navegador
        resposta.set_cookie(key="sessao_usuario", value=usuario.username, httponly=True)
        return resposta
        
    except ValueError as erro:
        # Devolve a tela de login com a mensagem de erro (ex: "Senha incorreta")
        return templates.TemplateResponse(
            name="login.html", 
            request=request,
            context={"erro": str(erro)}
        )

@router.get("/dashboard")
async def painel_usuario(request: Request, usuario: Usuario = Depends(obter_usuario_logado)):
    """A dependência 'obter_usuario_logado' já verifica os cookies.
    Busca no '_mapa_usernames' e devolve o objeto correto do '_banco_por_id'.
    Se o cookie não existir, ela mesma já expulsa o usuário para a tela de erro 401.
    """
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"usuario": usuario}
    )

@router.get("/logout")
async def sair(request: Request):
    resposta = RedirectResponse(url="/")
    resposta.delete_cookie("sessao_usuario")
    return resposta