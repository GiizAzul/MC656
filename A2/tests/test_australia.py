from src import EleicaoAustralia

def test_vitoria_maioria_simples():
    candidatos = ['Caio', 'Gi', 'Juh', 'Leo', 'Samuel']
    cedulas = [
        ['Samuel', 'Caio', 'Gi', 'Juh', 'Leo'],
        ['Samuel', 'Leo', 'Juh', 'Caio', 'Gi'],
        ['Caio', 'Gi', 'Juh', 'Leo', 'Samuel']
    ]
    eleicao = EleicaoAustralia(candidatos, cedulas)
    assert eleicao.apurar_vencedor() == 'Samuel'

def test_vitoria_por_eliminacao_com_transferencia():
    candidatos = ['Caio', 'Gi', 'Juh', 'Leo', 'Samuel']
    cedulas = [
        ['Caio', 'Juh', 'Gi', 'Samuel', 'Leo'],
        ['Caio', 'Gi', 'Juh', 'Leo', 'Samuel'],
        ['Samuel', 'Leo', 'Juh', 'Gi', 'Caio'],
        ['Samuel', 'Gi', 'Juh', 'Caio', 'Leo'],
        ['Gi', 'Samuel', 'Juh', 'Leo', 'Caio'],
    ]
    eleicao = EleicaoAustralia(candidatos, cedulas)
    assert eleicao.apurar_vencedor() == 'Gi'