from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from src.autenticacao.base import Usuario

async def obter_usuario_logado(request: Request) -> Usuario:
    """Extrai o usuário do cookie. Se não existir, expulsa para o login."""
    username_logado = request.cookies.get("sessao_usuario")
    if not username_logado:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    banco = request.app.state.banco_auth
    usuario = banco._banco.get(username_logado)
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Sessão inválida") # Talvez essa handling seja ruim pois é um resultado esperado, temos que mudar depois para um tratamento de objetos de excessão
        
    return usuario