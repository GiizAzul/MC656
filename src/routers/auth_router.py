from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.autenticacao.caco import EstudanteCACo, GestaoCACo
from src.autenticacao.australia import CandidatoAustralia, EleitorAustralia
from src.autenticacao.botc import JogadorBOTC, StoryTellerBOTC

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/cadastro", response_class=HTMLResponse)
async def tela_cadastro(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

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
    if senha != senha_confirma:
        return templates.TemplateResponse("cadastro.html", {"request": request, "erro": "Senhas não conferem."})
        
    banco = request.app.state.banco_auth
    
    # Simula o auto-incremento de ID
    novo_id = len(banco._banco) + 1 # Isso tem que ser mudado após a lógica de criação de ID's para novos usuários ser implementada
    
    try:
        # Análise condicional do tipo de usuário
        if tipo_conta == "CACO_ESTUDANTE":
            if not ra or not ra.isnumeric():
                raise ValueError("RA inválido.")
            novo_usuario = EstudanteCACo(novo_id, username, senha, nome_real, int(ra))
        elif tipo_conta == "CACO_GESTAO":
            novo_usuario = GestaoCACo(novo_id, username, senha, nome_real)
        elif tipo_conta == "AUSTRALIA_ELEITOR":
            novo_usuario = EleitorAustralia(novo_id, username, senha, nome_real)
        elif tipo_conta == "AUSTRALIA_CANDIDATO":
            novo_usuario = CandidatoAustralia(novo_id, username, senha, nome_real)
        elif tipo_conta == "BOTC_JOGADOR":
            novo_usuario = JogadorBOTC(novo_id, username, senha, nome_real)
        elif tipo_conta == "BOTC_STORYTELLER":
            novo_usuario = StoryTellerBOTC(novo_id, username, senha, nome_real)
        else:
            raise ValueError("Tipo de conta desconhecido.")
            
        banco.registrar(novo_usuario)
        
        # Faz o login automático após cadastro
        resposta = RedirectResponse(url="/dashboard", status_code=302)
        resposta.set_cookie(key="sessao_usuario", value=username, httponly=True)
        return resposta
        
    except ValueError as erro:
        return templates.TemplateResponse("cadastro.html", {"request": request, "erro": str(erro)})

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
            "login.html", 
            {"request": request, "erro": str(erro)}
        )

@router.get("/dashboard")
async def painel_usuario(request: Request):
    # Verifica o cookie para saber se está logado
    username_logado = request.cookies.get("sessao_usuario")
    if not username_logado:
        return RedirectResponse(url="/")
        
    banco = request.app.state.banco_auth
    usuario = banco._banco.get(username_logado)
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "usuario": usuario}
    )

@router.get("/logout")
async def sair(request: Request):
    resposta = RedirectResponse(url="/")
    resposta.delete_cookie("sessao_usuario")
    return resposta