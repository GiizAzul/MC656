from enum import Enum

from src.interfaces import SistemaEleitoral


class StatusJogador(str, Enum):
    """Estados de vida e disponibilidade de voto de um jogador em Blood on the Clocktower."""
    VIVO = "Vivo"
    MORTO_COM_FANTASMA = "Morto (Com Voto)"
    MORTO_SEM_FANTASMA = "Morto (Sem Voto)"


class JogadorBotC:
    """Entidade que representa um jogador em Blood on the Clocktower."""

    def __init__(
        self,
        id_jogador: str,
        nome: str,
        status: StatusJogador = StatusJogador.VIVO,
    ):
        if not id_jogador or not isinstance(id_jogador, str):
            raise ValueError("O identificador do jogador deve ser um User_ID válido.")
        if not nome or not isinstance(nome, str):
            raise ValueError("O nome do jogador deve ser um texto válido.")

        self.id_jogador = id_jogador
        self.nome = nome
        self.status = status

    def pode_votar(self) -> bool:
        """Indica se o jogador possui elegibilidade para votar."""
        return self.status in (StatusJogador.VIVO, StatusJogador.MORTO_COM_FANTASMA)

    def consumir_voto_fantasma(self) -> bool:
        """
        Consome o voto fantasma se o jogador estiver MORTO_COM_FANTASMA.
        Retorna True caso o voto tenha sido consumido, alterando para MORTO_SEM_FANTASMA.
        """
        if self.status == StatusJogador.MORTO_COM_FANTASMA:
            self.status = StatusJogador.MORTO_SEM_FANTASMA
            return True
        return False


class SistemaEleitoralBotC(SistemaEleitoral):
    """
    Sistema de votação para Blood on the Clocktower.
    Para alguém ser executado, deve receber quantidade de votos >= metade
    dos jogadores vivos. Em caso de empate no maior número de votos, ninguém é executado.
    """

    def __init__(self, jogadores_vivos: int):
        if jogadores_vivos <= 0:
            raise ValueError("O número de jogadores vivos deve ser maior que zero.")
        self.jogadores_vivos = jogadores_vivos
        # Dicionário mapeia User_ID do candidato -> quantidade de votos
        self.votos: dict[str, int] = {}

    def registrar_votacao(self, candidato_id: str, num_votos: int):
        """Registra votos utilizando o User_ID imutável do candidato."""
        if not candidato_id or not isinstance(candidato_id, str):
            raise ValueError("O identificador do candidato deve ser um User_ID válido.")
        if num_votos < 0:
            raise ValueError("O número de votos não pode ser negativo.")
        if num_votos > self.jogadores_vivos:
            raise ValueError("O número de votos não pode ser maior que a quantidade de jogadores.")
        self.votos[candidato_id] = num_votos

    def apurar_vencedor(self) -> str | None:
        """Retorna o User_ID do executado ou None se houver empate/sem maioria."""
        if not self.votos:
            return None

        maioria = self.jogadores_vivos / 2

        candidatos_validos = {cid: v for cid, v in self.votos.items() if v >= maioria}

        if not candidatos_validos:
            return None

        maior_voto = max(candidatos_validos.values())

        vencedores = [cid for cid, v in candidatos_validos.items() if v == maior_voto]

        if len(vencedores) > 1:
            return None

        return vencedores[0]
