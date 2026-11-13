from .interfaces import SistemaEleitoral


class EleicaoAustralia(SistemaEleitoral):
    """Classe para apuração utilizando voto único transferível."""

    def __init__(
        self,
        candidatos_ids: list[str],
        cedulas: list[list[str]],
        partidos_candidatos: dict[str, list[str]] | None = None,
    ):
        # Inicia no estado AguardandoVotacao (padrão State de SistemaEleitoral)
        super().__init__()

        self.candidatos_oficiais = set(candidatos_ids)
        self.candidatos = {cid: True for cid in candidatos_ids}
        self.cedulas: list[list[str]] = []
        self.partidos_candidatos = {
            partido: list(candidatos)
            for partido, candidatos in (partidos_candidatos or {}).items()
        }

        candidatos_com_partido = [
            candidato
            for candidatos in self.partidos_candidatos.values()
            for candidato in candidatos
        ]
        if len(candidatos_com_partido) != len(set(candidatos_com_partido)):
            raise ValueError("Cada candidato deve pertencer a apenas um partido.")
        if not set(candidatos_com_partido).issubset(self.candidatos_oficiais):
            raise ValueError("Os partidos não podem conter candidatos não registrados na eleição.")
        if any(not partido.strip() or not candidatos for partido, candidatos in self.partidos_candidatos.items()):
            raise ValueError("Cada partido deve ter um nome e pelo menos um candidato.")
        if partidos_candidatos and set(candidatos_com_partido) != self.candidatos_oficiais:
            raise ValueError("Todos os candidatos devem pertencer a um partido para habilitar o ranking por partidos.")

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

    def converter_ranking_partidos(self, preferencias: list[str]) -> list[str]:
        """Valida um ranking completo de partidos e o converte em ranking de candidatos.

        Candidatos do mesmo partido seguem a ordem informada em `partidos_candidatos`.
        Isso permite que o motor aceite votos por partido sem alterar o formato das
        cédulas usado pela apuração existente.
        """
        if not self.partidos_candidatos:
            raise ValueError("O ranking por partidos não está configurado nesta eleição.")
        if not isinstance(preferencias, list):
            raise TypeError("O ranking de partidos deve ser uma lista ordenada.")

        partidos_registrados = set(self.partidos_candidatos)
        partidos_votados = set(preferencias)
        faltantes = [partido for partido in self.partidos_candidatos if partido not in partidos_votados]
        duplicados = list(dict.fromkeys(
            partido for partido in preferencias if preferencias.count(partido) > 1
        ))
        inexistentes = [partido for partido in preferencias if partido not in partidos_registrados]

        erros = []
        if faltantes:
            erros.append("Faltam partidos no ranking: " + ", ".join(faltantes) + ".")
        if duplicados:
            erros.append("Partidos repetidos no ranking: " + ", ".join(duplicados) + ".")
        if inexistentes:
            erros.append("Partidos não registrados: " + ", ".join(dict.fromkeys(inexistentes)) + ".")
        if erros:
            raise ValueError(" ".join(erros))

        return [
            candidato
            for partido in preferencias
            for candidato in self.partidos_candidatos[partido]
        ]

    def converter_posicoes_partidos(self, posicoes: dict[str, object]) -> list[str]:
        """Valida posições de 1 a N e retorna os partidos em ordem de preferência."""
        if not self.partidos_candidatos:
            raise ValueError("O ranking por partidos não está configurado nesta eleição.")
        if not isinstance(posicoes, dict):
            raise TypeError("As posições dos partidos devem ser informadas em um dicionário.")

        partidos = list(self.partidos_candidatos)
        ranking: list[tuple[int, str]] = []
        partidos_sem_posicao = []
        posicoes_invalidas = []

        for partido in partidos:
            valor = posicoes.get(partido)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                partidos_sem_posicao.append(partido)
                continue
            if isinstance(valor, bool):
                posicoes_invalidas.append(partido)
                continue
            if isinstance(valor, int):
                posicao = valor
            elif isinstance(valor, str) and valor.strip().isdigit():
                posicao = int(valor.strip())
            else:
                posicoes_invalidas.append(partido)
                continue
            ranking.append((posicao, partido))

        partidos_desconhecidos = [partido for partido in posicoes if partido not in self.partidos_candidatos]
        valores = [posicao for posicao, _ in ranking]
        repetidas = sorted({posicao for posicao in valores if valores.count(posicao) > 1})
        faltantes = sorted(set(range(1, len(partidos) + 1)) - set(valores))
        fora_do_intervalo = sorted({posicao for posicao in valores if posicao < 1 or posicao > len(partidos)})

        erros = []
        if partidos_sem_posicao:
            erros.append("Partidos sem posição: " + ", ".join(partidos_sem_posicao) + ".")
        if posicoes_invalidas:
            erros.append("Posições inválidas para: " + ", ".join(posicoes_invalidas) + ".")
        if repetidas:
            erros.append("Posições repetidas: " + ", ".join(map(str, repetidas)) + ".")
        if faltantes:
            erros.append("Posições faltantes: " + ", ".join(map(str, faltantes)) + ".")
        if fora_do_intervalo:
            erros.append("Posições fora do intervalo 1 a N: " + ", ".join(map(str, fora_do_intervalo)) + ".")
        if partidos_desconhecidos:
            erros.append("Partidos não registrados: " + ", ".join(partidos_desconhecidos) + ".")
        if erros:
            raise ValueError(" ".join(erros))

        ranking.sort(key=lambda item: item[0])
        return [partido for _, partido in ranking]

    def apurar_voto_partidos(self, eleitor_id: str, preferencias: list[str]) -> None:
        """Registra preferência por partidos respeitando o ciclo de estados da eleição."""
        if self.estado.nome != "VOTACAO":
            self.apurar_voto(eleitor_id, preferencias)
        cedula = self.converter_ranking_partidos(preferencias)
        self.apurar_voto(eleitor_id, cedula)

    def apurar_voto_partidos_por_posicao(
        self, eleitor_id: str, posicoes: dict[str, object]
    ) -> None:
        """Valida posições do eleitor e registra a cédula pelo ciclo de estados."""
        if self.estado.nome != "VOTACAO":
            self.apurar_voto(eleitor_id, [])
        preferencias = self.converter_posicoes_partidos(posicoes)
        self.apurar_voto_partidos(eleitor_id, preferencias)

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
            raise TypeError("Erro de cédula inválida: o voto deve ser uma lista ordenada de candidatos.")

        # Garante voto único
        if eleitor_id in self.votantes:
            raise ValueError("Você já registrou seu voto nesta eleição.")

        self._validar_cedula(voto, "cédula")

        self.cedulas.append(voto[:])
        self.votantes.add(eleitor_id)
