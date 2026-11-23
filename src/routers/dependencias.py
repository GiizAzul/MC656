from fastapi import Depends, Request

from src.autenticacao.autorizacao import ControleDeAcesso
from src.autenticacao.base import Usuario


class RequerRedirecionamentoException(Exception):
    """Exceção customizada para forçar o redirect na Web."""

async def obter_usuario_logado(request: Request) -> Usuario:
    username_logado = request.cookies.get("sessao_usuario")
    if not username_logado:
        raise RequerRedirecionamentoException()
        
    banco = request.app.state.banco_auth
    
    # Busca o ID usando o username no novo mapa
    user_id = banco._mapa_usernames.get(username_logado)
    if not user_id:
        raise RequerRedirecionamentoException()
         
    # Busca o objeto usuário usando o ID
    usuario = banco._banco_por_id.get(user_id)
    if not usuario:
        raise RequerRedirecionamentoException()
        
    return usuario

controle_acesso = ControleDeAcesso()

def exigir_autorizacao_rota(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
) -> Usuario:
    controle_acesso.acessar_recurso(usuario, request.url.path)
    return usuario