import pytest
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
    assert eleicao.apurar_vencedor() == 'Samuel'

def test_listas_vazias():
    eleicao_sem_candidato = EleicaoAustralia([], [[]])
    assert eleicao_sem_candidato.apurar_vencedor() is None

    eleicao_sem_voto = EleicaoAustralia(['Caio', 'Gi'], [])
    assert eleicao_sem_voto.apurar_vencedor() is None

def test_rejeita_cedula_incompleta():
    candidatos = ['Caio', 'Gi', 'Juh']
    # Faltou ranquear a Juh na primeira cédula
    cedulas_erradas = [['Caio', 'Gi'], ['Juh', 'Caio', 'Gi']]
    
    # Verifica se o sistema levanta um ValueError adequadamente
    with pytest.raises(ValueError, match="Você deve ranquear exatamente todos os 3 candidatos"):
        EleicaoAustralia(candidatos, cedulas_erradas)

def test_rejeita_cedula_com_candidato_falso_ou_duplicado():
    candidatos = ['Samuel', 'Leo']
    # Votou no Samuel duas vezes
    cedulas_fraudadas = [['Samuel', 'Samuel']]
    
    with pytest.raises(ValueError, match="candidatos duplicados ou não registrados"):
        EleicaoAustralia(candidatos, cedulas_fraudadas)