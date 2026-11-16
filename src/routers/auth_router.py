from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.autenticacao.base import Usuario
from src.autenticacao.factory import UsuarioFactory

from .dependencias import obter_usuario_logado

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/admin", response_class=HTMLResponse)
async def painel_admin(
    request: Request, 
    usuario: Annotated [Usuario, Depends(obter_usuario_logado)]
):
    # Impede que usuários comuns entrem na tela de gestão
    if "GESTAO" not in usuario.escopo and "STORYTELLER" not in usuario.escopo:
        return RedirectResponse(url="/dashboard")
        
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={"usuario": usuario}
    )

@router.get("/cadastro", response_class=HTMLResponse)
async def tela_cadastro(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="cadastro.html", 
        context={}
    )

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

        # Delegação da lógica de criação polimórfica e validações para a Factory
        novo_usuario = UsuarioFactory.criar(tipo_conta, username, senha, nome_real, ra)

        usuario_registrado = banco.registrar(novo_usuario)
        id_final = usuario_registrado.id if usuario_registrado else novo_usuario.id

        # Adiciona alunos e gestores novos na lista de eleitores da assembleia ativa 
        if tipo_conta in ("CACO_ESTUDANTE", "CACO_GESTAO"):
            eleicao_caco = request.app.state.eleicao_caco
            eleicao_caco.alunos_cadastrados.add(id_final)
            eleicao_caco.eleitores.add(id_final)

        # Faz o login automático após cadastro
        resposta = RedirectResponse(url="/dashboard", status_code=302)
        resposta.set_cookie(
            key="sessao_usuario",
            value=username,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
        )
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


@router.post("/adicionar-escopo")
async def adicionar_escopo_usuario(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    tipo_conta: str = Form(...),
    ra: str = Form(None),
):
    """Permite que um usuário já logado habilite outro escopo/contexto na mesma conta."""
    try:
        temp_user = UsuarioFactory.criar(
            tipo_conta, usuario.username, "senha_temp", usuario.nome_real, ra
        )
        ra_int = getattr(temp_user, "ra", None)
        usuario.adicionar_escopo(temp_user.escopo, ra=ra_int)

        if ra_int is not None:
            request.app.state.banco_auth._mapa_usernames[str(ra_int)] = usuario.id

        if tipo_conta in ("CACO_ESTUDANTE", "CACO_GESTAO"):
            eleicao_caco = request.app.state.eleicao_caco
            eleicao_caco.alunos_cadastrados.add(usuario.id)
            eleicao_caco.eleitores.add(usuario.id)

        return RedirectResponse(url="/dashboard", status_code=302)
    except ValueError as erro:
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"usuario": usuario, "erro": str(erro)},
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
        resposta.set_cookie(
            key="sessao_usuario", 
            value=usuario.username, 
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax"
        )
        return resposta
        
    except ValueError as erro:
        # Devolve a tela de login com a mensagem de erro (ex: "Senha incorreta")
        return templates.TemplateResponse(
            name="login.html", 
            request=request,
            context={"erro": str(erro)}
        )

@router.get("/dashboard")
async def painel_usuario(request: Request, usuario: Annotated [Usuario, Depends(obter_usuario_logado)]):
    """A dependência 'obter_usuario_logado' já verifica os cookies.
    Busca no '_mapa_usernames' e devolve o objeto correto do '_banco_por_id'.
    Se o cookie não existir, ela mesma já expulsa o usuário para a tela de erro 401.
    """
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"usuario": usuario}
    )

@router.get("/api/me")
async def obter_perfil_json(
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
):
    """Endpoint JSON consumido pelo frontend para obter sessão e escopos."""
    return JSONResponse({
        "id": usuario.id,
        "username": usuario.username,
        "nome_real": usuario.nome_real,
        "escopo": usuario.escopo,
        "ra": getattr(usuario, "ra", None),
    })

@router.get("/logout")
async def sair(request: Request):
    resposta = RedirectResponse(url="/")
    resposta.delete_cookie("sessao_usuario")
    return resposta