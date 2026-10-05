from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from src.autenticacao.base import Usuario

class RequerRedirecionamentoException(Exception):
    """Exceção customizada para forçar o redirect na Web."""
    pass

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