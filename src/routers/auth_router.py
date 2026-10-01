from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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