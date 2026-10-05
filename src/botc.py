from src.interfaces import SistemaEleitoral


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
