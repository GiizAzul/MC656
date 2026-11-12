from src.autenticacao.australia import CandidatoAustralia, EleitorAustralia
from src.autenticacao.base import Usuario
from src.autenticacao.botc import JogadorBOTC, StoryTellerBOTC
from src.autenticacao.caco import EstudanteCACo, GestaoCACo


class UsuarioFactory:
    @staticmethod
    def criar(tipo_conta: str, username: str, senha: str, nome_real: str, ra: str | None = None) -> Usuario:
        if tipo_conta == "CACO_ESTUDANTE":
            if not ra or not ra.isnumeric():
                raise ValueError("RA inválido. Tente novamente.")
            return EstudanteCACo(username, senha, nome_real, int(ra))
        elif tipo_conta == "CACO_GESTAO":
            return GestaoCACo(username, senha, nome_real)
        elif tipo_conta == "AUSTRALIA_ELEITOR":
            return EleitorAustralia(username, senha, nome_real)
        elif tipo_conta == "AUSTRALIA_CANDIDATO":
            return CandidatoAustralia(username, senha, nome_real)
        elif tipo_conta == "BOTC_JOGADOR":
            return JogadorBOTC(username, senha, nome_real)
        elif tipo_conta == "BOTC_STORYTELLER":
            return StoryTellerBOTC(username, senha, nome_real)
        else:
            raise ValueError("Tipo de conta desconhecido.")