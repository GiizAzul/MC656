from .base import Usuario

class ErroAcessoNaoAutorizado(Exception):
    """Exceção customizada para simular um HTTP 403 - Forbidden"""
    def __init__(self, mensagem: str, painel_redirecionamento: str):
        super().__init__(mensagem)
        self.painel_redirecionamento = painel_redirecionamento


class ControleDeAcesso:
    """Gerencia o acesso baseado estritamente nos escopos existentes no domínio."""
    
    # Traduz o prefixo das classes (BOTC, CACO, AUSTRALIA)
    MAPA_SCOPES = {
        "BOTC": "SCOPE_BCT", 
        "CACO": "SCOPE_CACO",
        "AUSTRALIA": "SCOPE_AUSTRALIA"
    }

    # (substituir pelos endpoints web)
    PAINEIS_INICIAIS = {
        "SCOPE_BCT": "painel_jogador_bct",
        "SCOPE_CACO": "painel_estudante_caco",
        "SCOPE_AUSTRALIA": "painel_eleitor_australia",
        "SCOPE_GLOBAL": "painel_global"
    }

    # Proteção das lógicas (substituir pelos endpoints web)
    RECURSOS_PROTEGIDOS = {
        "painel_jogador_bct": "SCOPE_BCT",
        "painel_estudante_caco": "SCOPE_CACO",
        "painel_eleitor_australia": "SCOPE_AUSTRALIA"
    }

    @classmethod
    def extrair_macro_scope(cls, usuario: Usuario) -> str:
        """Lê o escopo nativo da sua classe (ex: 'BOTC_JOGADOR') e converte para 'SCOPE_BCT'."""
        prefixo = usuario.escopo.split("_")[0]
        return cls.MAPA_SCOPES.get(prefixo, "SCOPE_GLOBAL")

    def despachar_apos_login(self, usuario: Usuario) -> str:
        """Retorna o identificador do painel correspondente ao perfil."""
        macro_scope = self.extrair_macro_scope(usuario)
        return self.PAINEIS_INICIAIS.get(macro_scope, "painel_global")

    def acessar_recurso(self, usuario: Usuario, recurso_solicitado: str) -> str:
        """Verifica permissão e levanta exceção 403 em caso de infração."""
        scope_necessario = self.RECURSOS_PROTEGIDOS.get(recurso_solicitado)
        
        # Se o recurso não tem proteção declarada, libera o acesso
        if not scope_necessario:
            return f"Acesso liberado para {recurso_solicitado}"

        scope_usuario = self.extrair_macro_scope(usuario)

        if scope_usuario != scope_necessario and scope_usuario != "SCOPE_GLOBAL":
            painel_nativo = self.despachar_apos_login(usuario)
            raise ErroAcessoNaoAutorizado(
                mensagem=f"HTTP 403: Acesso Não Autorizado. Escopo {scope_usuario} bloqueado.",
                painel_redirecionamento=painel_nativo
            )
            
        return f"Acesso concedido ao {recurso_solicitado}."