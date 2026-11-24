from typing import ClassVar

from .base import Usuario


class ErroAcessoNaoAutorizado(Exception):
    """Exceção customizada para simular um HTTP 403 - Forbidden"""
    def __init__(self, mensagem: str, painel_redirecionamento: str):
        super().__init__(mensagem)
        self.painel_redirecionamento = painel_redirecionamento


class ControleDeAcesso:
    """Gerencia o acesso baseado estritamente nos escopos existentes no domínio."""
    
    # 1. Traduz o prefixo das suas classes (BOTC, CACO, AUSTRALIA) para o exigido na história
    MAPA_SCOPES: ClassVar[dict[str, str]] = {
        "BOTC": "SCOPE_BCT", 
        "CACO": "SCOPE_CACO",
        "AUSTRALIA": "SCOPE_AUSTRALIA"
    }

    # 2. Painéis iniciais definidos estritamente pela sua História de Usuário
    PAINEIS_INICIAIS: ClassVar[dict[str, str]] = {
        "SCOPE_BCT": "/botc/partida",
        "SCOPE_CACO": "/caco/assembleia",
        "SCOPE_AUSTRALIA": "/australia/votar",
        "SCOPE_GLOBAL": "/dashboard",
    }

    # 3. Proteção das lógicas (substitua pelos endpoints web quando forem criados)
    RECURSOS_PROTEGIDOS: ClassVar[dict[str, str]] = {
        "/botc": "SCOPE_BCT",
        "/caco": "SCOPE_CACO",
        "/australia": "SCOPE_AUSTRALIA",
    }

    @classmethod
    def extrair_macro_scopes(cls, usuario: Usuario) -> set[str]:
        escopo_raw = getattr(usuario, "escopo", "") or ""
        partes = [parte.strip().upper() for parte in escopo_raw.split(",") if parte.strip()]
        macro_scopes: set[str] = set()

        for parte in partes:
            if parte == "ADMIN" or parte.startswith("GLOBAL"):
                macro_scopes.add("SCOPE_GLOBAL")
            elif parte.startswith(("BCT", "BOTC")):
                macro_scopes.add("SCOPE_BCT")
            elif parte.startswith("CACO"):
                macro_scopes.add("SCOPE_CACO")
            elif parte.startswith("AUSTRALIA"):
                macro_scopes.add("SCOPE_AUSTRALIA")
            # Escopos não reconhecidos são ignorados (nunca viram SCOPE_GLOBAL por padrão)

        return macro_scopes

    @classmethod
    def extrair_macro_scope(cls, usuario: Usuario) -> str:
        """Lê o escopo nativo da sua classe (ex: 'BOTC_JOGADOR') e converte para 'SCOPE_BCT'."""
        scopes = cls.extrair_macro_scopes(usuario)
        if "SCOPE_GLOBAL" in scopes or len(scopes) != 1:
            return "SCOPE_GLOBAL"
        return next(iter(scopes))
    
    @classmethod
    def _obter_scope_necessario(cls, recurso_solicitado: str) -> str | None:
        """Identifica o escopo exigido comparando pelo prefixo da URL."""
        caminho = recurso_solicitado.rstrip("/") or "/"
        for prefixo, scope in cls.RECURSOS_PROTEGIDOS.items():
            if caminho == prefixo or caminho.startswith(f"{prefixo}/"):
                return scope
        return None

    def despachar_apos_login(self, usuario: Usuario) -> str:
        """Retorna o identificador do painel correspondente ao perfil."""
        macro_scope = self.extrair_macro_scope(usuario)
        return self.PAINEIS_INICIAIS.get(macro_scope, "/dashboard")

    def acessar_recurso(self, usuario: Usuario, recurso_solicitado: str) -> str:
        """Verifica permissão e levanta exceção 403 em caso de infração."""
        scope_necessario = self._obter_scope_necessario(recurso_solicitado)
        
        # Se o recurso não tem proteção declarada, libera o acesso
        if not scope_necessario:
            return f"Acesso liberado para {recurso_solicitado}"

        scopes_usuario = self.extrair_macro_scopes(usuario)

        if scope_necessario not in scopes_usuario and "SCOPE_GLOBAL" not in scopes_usuario:
            painel_nativo = self.despachar_apos_login(usuario)
            raise ErroAcessoNaoAutorizado(
                mensagem=f"HTTP 403: Acesso Não Autorizado. Permissão {scope_necessario} necessária.",
                painel_redirecionamento=painel_nativo,
            )
            
        return f"Acesso concedido ao {recurso_solicitado}."