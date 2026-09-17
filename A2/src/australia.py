def calcular_vencedor_australia(cedulas: list[list[str]], candidatos: list[str]) -> str | None:
    """
    Calcula o vencedor usando o sistema de ranqueamento da Austrália.
    cedulas: Uma lista de listas, onde cada sublista é o ranking de um eleitor.
    """
    if not cedulas:
        return None

    # Dicionário controlando o status do candidato
    controle_candidatos = {nome: True for nome in candidatos}
    # Cria uma cópia para não alterar a original
    cedulas_ativas = [cedula[:] for cedula in cedulas if cedula]

    while True:
        contagem = {nome: 0 for nome, ativo in candidatos.items() if ativo}
        total_votos = 0

        # Conta os votos de primeira preferência
        for cedula in cedulas_ativas:
            # Varre o ranking do eleitor e dá o voto para o primeiro candidato ativo que achar
            for opcao in cedula:
                if candidatos.get(opcao):
                    contagem[opcao] += 1
                    total_votos += 1
                    break # Pula para o próximo eleitor
        if total_votos == 0:
            return None

        # Verifica se alguém atingiu maioria absoluta
        for candidato, votos in contagem.items():
            if votos > total_votos / 2:
                return candidato

        # Encontra o candidato com menos votos para ser eliminado
        min_votos = min(contagem.values())
        # Elimina mudando o status pra inativo
        candidatos[min_votos] = False
        # Condição de parada
        ativos = [c for c, ativo in self.candidatos.items() if ativo]
            if len(ativos) == 1:
                return ativos[0]
            elif len(ativos) == 0:
                return None
