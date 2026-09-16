def calcular_vencedor_australia(cedulas: list[list[str]]) -> str | None:
    """
    Calcula o vencedor usando o sistema de ranqueamento da Austrália.
    cedulas: Uma lista de listas, onde cada sublista é o ranking de um eleitor.
    Ex: [['Alice', 'Bob'], ['Bob', 'Alice'], ['Alice']]
    """
    if not cedulas:
        return None

    # Cria uma cópia para não alterar a original
    cedulas_ativas = [cedula[:] for cedula in cedulas if cedula]

    while True:
        contagem = {}
        total_votos = 0

        # Conta os votos de primeira preferência
        for cedula in cedulas_ativas:
            if cedula:
                primeira_opcao = cedula[0]
                contagem[primeira_opcao] = contagem.get(primeira_opcao, 0) + 1
                total_votos += 1

        if total_votos == 0:
            return None

        # Verifica se alguém atingiu maioria absoluta
        for candidato, votos in contagem.items():
            if votos > total_votos / 2:
                return candidato

        # Encontra o candidato com menos votos para ser eliminado
        min_votos = min(contagem.values())
        candidatos_para_eliminar = [c for c, v in contagem.items() if v == min_votos]
        eliminado = candidatos_para_eliminar[0] # Simplificação: elimina o primeiro em caso de empate

        # Remove o candidato eliminado de todas as cédulas (transferindo o voto)
        for cedula in cedulas_ativas:
            while eliminado in cedula:
                cedula.remove(eliminado)
