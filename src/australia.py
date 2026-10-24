from .interfaces import SistemaEleitoral


class EleicaoAustralia(SistemaEleitoral):
    """Classe para apuração utilizando voto único transferível."""

    def __init__(self, candidatos_ids: list[str], cedulas: list[list[str]]):
        # Inicia no estado AguardandoVotacao (padrão State de SistemaEleitoral)
        super().__init__()

        self.candidatos_oficiais = set(candidatos_ids)
        self.candidatos = {cid: True for cid in candidatos_ids}
        self.cedulas: list[list[str]] = []

        # Registro de quem já votou (cédulas carregadas no construtor são anônimas)
        self.votantes: set[str] = set()

        # Validação que os dados são íntegros com os candidatos registrados
        for i, cedula in enumerate(cedulas):
            self._validar_cedula(cedula, f"cédula {i+1}")
            self.cedulas.append(cedula[:])

    def _validar_cedula(self, cedula: list[str], identificacao: str) -> None:
        """Garante que a cédula ranqueia todos os candidatos, sem repetir nem inventar nomes."""
        num_candidatos = len(self.candidatos_oficiais)

        # Verifica se tem o tamanho exato com todos os candidatos escolhidos
        if len(cedula) != num_candidatos:
            raise ValueError(f"Erro de {identificacao} inválida: Você deve ranquear exatamente todos os {num_candidatos} candidatos.")

        # Verifica se não está colocando candidato que não existem, anular o voto ou repetindo ele
        if set(cedula) != self.candidatos_oficiais:
            raise ValueError(f"Erro de {identificacao} inválida: A cédula contém candidatos duplicados ou não registrados.")

    def _contar_primeiras_preferencias(self) -> dict[str, int]:
        """Método privado para contabilizar os votos válidos da rodada atual."""
        contagem = {cid: 0 for cid, ativo in self.candidatos.items() if ativo}
        
        for cedula in self.cedulas:
            # Varre o ranking do eleitor e dá o voto para o primeiro candidato ativo que achar
            for opcao_id in cedula:
                if self.candidatos.get(opcao_id):
                    contagem[opcao_id] += 1
                    break  # Pula para o próximo eleitor
        return contagem

    def apurar_vencedor(self) -> str | None:
        """Executa os turnos de eliminação até encontrar o vencedor."""
        if not self.candidatos or not self.cedulas: # Podia resumir o condicional mas assim fica mais legível
            return None

        while True:
            contagem = self._contar_primeiras_preferencias()
            total_votos_validos = sum(contagem.values())

            if total_votos_validos == 0:
                return None

            # Verifica se alguém atingiu maioria absoluta
            for candidato_id, votos in contagem.items():
                if votos > total_votos_validos / 2:
                    return candidato_id

            # Encontra o candidato com menos votos
            candidato_menos_votado = min(contagem, key=contagem.get)
            
            # Elimina o candidato mudando o status para inativo
            self.candidatos[candidato_menos_votado] = False

            # Condição de parada (se sobrou apenas 1 ativo, ele vence)
            ativos = [c for c, ativo in self.candidatos.items() if ativo]
            if len(ativos) == 1:
                return ativos[0]
            elif len(ativos) == 0:
                return None
            
    def registrar_voto(self, eleitor_id: str, voto: list[str]) -> None:
        """Registra a cédula de um eleitor.

        `voto` é a lista de candidatos em ordem de preferência (1ª posição = maior prioridade).
        Use `apurar_voto` para respeitar o estado da votação; este método só registra.
        """
        if not isinstance(voto, list):
            raise ValueError("Erro de cédula inválida: o voto deve ser uma lista ordenada de candidatos.")

        # Garante voto único
        if eleitor_id in self.votantes:
            raise ValueError("Você já registrou seu voto nesta eleição.")

        self._validar_cedula(voto, "cédula")

        self.cedulas.append(voto[:])
        self.votantes.add(eleitor_id)
