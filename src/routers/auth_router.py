from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.autenticacao.autorizacao import ControleDeAcesso
from src.autenticacao.base import Usuario
from src.autenticacao.factory import UsuarioFactory
from src.database import salvar_estado_sql

from .dependencias import (
    SESSION_TTL_SECONDS,
    gerar_token_sessao,
    obter_usuario_logado,
)

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

controle_acesso = ControleDeAcesso()

def _definir_cookie_sessao(resposta, request: Request, username: str) -> None:
    resposta.set_cookie(
        key="sessao_usuario",
        value=gerar_token_sessao(username),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )

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
        salvar_estado_sql("banco_auth", request.app.state.banco_auth)

        # Adiciona alunos e gestores novos na lista de eleitores da assembleia ativa 
        if tipo_conta in ("CACO_ESTUDANTE", "CACO_GESTAO"):
            eleicao_caco = request.app.state.eleicao_caco
            eleicao_caco.alunos_cadastrados.add(id_final)
            eleicao_caco.eleitores.add(id_final)
            salvar_estado_sql("eleicao_caco", request.app.state.eleicao_caco)

        # Faz o login automático após cadastro
        rota_destino = controle_acesso.despachar_apos_login(novo_usuario)
        resposta = RedirectResponse(url=rota_destino, status_code=302)
        _definir_cookie_sessao(resposta, request, username)
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
    pede_json = "application/json" in request.headers.get("accept", "")
    try:
        temp_user = UsuarioFactory.criar(
            tipo_conta, usuario.username, "senha_temp", usuario.nome_real, ra
        )
        ra_int = getattr(temp_user, "ra", None)
        
        banco = request.app.state.banco_auth
        banco.vincular_escopo(usuario, temp_user.escopo, ra=ra_int)
        salvar_estado_sql("banco_auth", request.app.state.banco_auth)

        if tipo_conta in ("CACO_ESTUDANTE", "CACO_GESTAO"):
            eleicao_caco = request.app.state.eleicao_caco
            eleicao_caco.alunos_cadastrados.add(usuario.id)
            eleicao_caco.eleitores.add(usuario.id)
            salvar_estado_sql("eleicao_caco", request.app.state.eleicao_caco)
        if pede_json:
            return JSONResponse({"ok": True, "escopo": usuario.escopo})
        rota_destino = controle_acesso.despachar_apos_login(usuario)
        return RedirectResponse(url=rota_destino, status_code=302)
    except ValueError as erro:
        if pede_json:
            return JSONResponse({"detail": str(erro)}, status_code=400)
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
        
        rota_destino = controle_acesso.despachar_apos_login(usuario)
        resposta = RedirectResponse(url=rota_destino, status_code=302)

        # Salva o ID/Username no Cookie do navegador
        _definir_cookie_sessao(resposta, request, usuario.username)
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

def _ler_campo(obj, campo: str, padrao=None):
    if isinstance(obj, dict):
        return obj.get(campo, padrao)
    return getattr(obj, campo, padrao)


@router.get("/api/votacao-ativa")
async def obter_votacao_ativa(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
):
    """Indica se o usuário possui alguma cédula/sala de votação em andamento."""
    escopos = usuario.escopo or ""

    # 1. Blood on the Clocktower: sala ativa em que o usuário está sentado ou é Storyteller
    if "BOTC" in escopos:
        salas = getattr(request.app.state, "salas_botc", {}) or {}
        for sala_id, sala in salas.items():
            if _ler_campo(sala, "encerrada", False):
                continue
            st_id = _ler_campo(sala, "storyteller_id", None)
            jogadores = _ler_campo(sala, "jogadores", []) or []
            if isinstance(jogadores, dict):
                ids_jogadores = set(jogadores.keys())
            else:
                ids_jogadores = {_ler_campo(j, "id", j) for j in jogadores}

            if usuario.id == st_id or usuario.id in ids_jogadores:
                giro = _ler_campo(sala, "giro", None)
                sistema = _ler_campo(sala, "sistema", None)
                giro_ativo = bool(
                    _ler_campo(giro, "ativo", False)
                    or _ler_campo(sistema, "giro_ativo", False)
                )
                return JSONResponse({
                    "rota": f"/botc/partida?partida_id={sala_id}",
                    "contexto": "BOTC",
                    "partida_id": sala_id,
                    "em_votacao": giro_ativo,
                })

    # 2. Assembleia CACo: pauta aberta em VOTACAO onde o usuário ainda não votou
    if "CACO" in escopos and "CACO_GESTAO" not in escopos:
        assembleias = getattr(request.app.state, "assembleias_caco", None)
        if isinstance(assembleias, dict):
            for asm_id, asm in assembleias.items():
                if _ler_campo(asm, "encerrada", False):
                    continue
                pautas = _ler_campo(asm, "pautas", []) or []
                lista_pautas = pautas.values() if isinstance(pautas, dict) else pautas
                for pauta in lista_pautas:
                    votaram = (
                        _ler_campo(pauta, "eleitores_votaram", None)
                        or _ler_campo(pauta, "votantes", set())
                        or set()
                    )
                    if _ler_campo(pauta, "estado", "") == "VOTACAO" and usuario.id not in votaram:
                        return JSONResponse({
                            "rota": f"/caco/assembleia?assembleia_id={asm_id}",
                            "contexto": "CACO",
                            "assembleia_id": asm_id,
                        })
        else:
            eleicao_caco = getattr(request.app.state, "eleicao_caco", None)
            votaram_caco = getattr(request.app.state, "eleitores_caco_votaram", set()) or set()
            estado_caco = getattr(_ler_campo(eleicao_caco, "estado", None), "name", "")
            if estado_caco == "VOTACAO" and usuario.id not in votaram_caco:
                return JSONResponse({
                    "rota": "/caco/assembleia",
                    "contexto": "CACO",
                })

    # 3. Eleição Austrália: eleição aberta em VOTACAO onde o eleitor ainda não votou
    if "AUSTRALIA_ELEITOR" in escopos:
        eleicao_aus = getattr(request.app.state, "eleicao_australia", None)
        votaram_aus = getattr(request.app.state, "eleitores_australia_votaram", set()) or set()
        estado_aus = getattr(_ler_campo(eleicao_aus, "estado", None), "name", "")
        if estado_aus == "VOTACAO" and usuario.id not in votaram_aus:
            return JSONResponse({
                "rota": "/australia/votar",
                "contexto": "AUSTRALIA",
            })

    return JSONResponse({"rota": None})

@router.get("/logout")
async def sair(request: Request):
    resposta = RedirectResponse(url="/", status_code=302)
    resposta.delete_cookie("sessao_usuario", path="/", samesite="lax")
    return resposta

@router.post("/logout")
async def sair_api(request: Request):
    resposta = JSONResponse({"ok": True})
    resposta.delete_cookie("sessao_usuario", path="/", samesite="lax")
    return resposta
