from fastapi import Request, HTTPException
from src.autenticacao.base import Usuario

async def obter_usuario_logado(request: Request) -> Usuario:
    """Extrai o usuário do cookie. Se não existir, expulsa para o login."""
    username_logado = request.cookies.get("sessao_usuario")
    if not username_logado:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    banco = request.app.state.banco_auth
    
    # Busca o ID usando o username no novo mapa
    user_id = banco._mapa_usernames.get(username_logado)
    if not user_id:
         raise HTTPException(status_code=401, detail="Sessão inválida: Usuário não encontrado.")
         
    # Busca o objeto usuário usando o ID
    usuario = banco._banco_por_id.get(user_id)
    if not usuario:
        raise HTTPException(status_code=401, detail="Sessão inválida: Objeto de usuário não encontrado.")

    # Talvez essas handlings de HTTPException sejam ruins pois são resultados esperados, temos que mudar depois para um tratamento de objetos de excessão
        
    return usuario