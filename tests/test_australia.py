import pytest

from src import EleicaoAustralia
from src.estados import AguardandoVotacao, EmVotacao, Encerrada


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

def test_rejeita_cedula_incompativel_com_candidatos():
    with pytest.raises(ValueError, match="Você deve ranquear exatamente todos os 0 candidatos."):
        EleicaoAustralia([], [['Gi']])

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

def test_empate_perfeito():
    """Testa o comportamento do algoritmo caso não haja maioria absoluta"""
    candidatos = ['Caio', 'Gi']
    cedulas = [
        ['Caio', 'Gi'],
        ['Gi', 'Caio']
    ]
    eleicao = EleicaoAustralia(candidatos, cedulas)
    vencedor = eleicao.apurar_vencedor()
    assert vencedor in ['Caio', 'Gi']

def test_votos_zerados_no_meio_da_apuracao():
    """Força a condição de total_votos_validos == 0 burlando a inicialização
    para testar se a trava de segurança dentro do laço while True funciona."""
    eleicao = EleicaoAustralia(['Samuel', 'Juh'], [['Juh', 'Samuel']])
    eleicao.cedulas = [] # Esvazia as cédulas artificialmente após a validação
    assert eleicao.apurar_vencedor() is None

# --- Registro de votos e integração com o padrão State (src/estados.py) ---

def test_inicia_aguardando_votacao():
    eleicao = EleicaoAustralia(['Caio', 'Gi'], [])
    assert isinstance(eleicao.estado, AguardandoVotacao)

def test_apurar_voto_registra_cedula_quando_em_votacao():
    eleicao = EleicaoAustralia(['Caio', 'Gi', 'Juh'], [])
    eleicao.iniciar_votacao()
    assert isinstance(eleicao.estado, EmVotacao)

    eleicao.apurar_voto('eleitor1', ['Gi', 'Juh', 'Caio'])

    assert eleicao.cedulas == [['Gi', 'Juh', 'Caio']]
    assert 'eleitor1' in eleicao.votantes

def test_apurar_voto_antes_de_iniciar_levanta_erro():
    eleicao = EleicaoAustralia(['Caio', 'Gi'], [])
    with pytest.raises(RuntimeError):
        eleicao.apurar_voto('eleitor1', ['Caio', 'Gi'])
    assert eleicao.cedulas == []

def test_apurar_voto_apos_encerrar_levanta_erro():
    eleicao = EleicaoAustralia(['Caio', 'Gi'], [])
    eleicao.iniciar_votacao()
    eleicao.encerrar_votacao()
    assert isinstance(eleicao.estado, Encerrada)
    with pytest.raises(RuntimeError):
        eleicao.apurar_voto('eleitor1', ['Caio', 'Gi'])

def test_registrar_voto_copia_a_cedula():
    eleicao = EleicaoAustralia(['Caio', 'Gi'], [])
    cedula = ['Caio', 'Gi']
    eleicao.registrar_voto('eleitor1', cedula)
    cedula.reverse()  # alterar a lista original não pode afetar a urna
    assert eleicao.cedulas == [['Caio', 'Gi']]

def test_registrar_voto_rejeita_voto_duplicado():
    eleicao = EleicaoAustralia(['Caio', 'Gi'], [])
    eleicao.registrar_voto('eleitor1', ['Caio', 'Gi'])
    with pytest.raises(ValueError, match="já registrou seu voto"):
        eleicao.registrar_voto('eleitor1', ['Gi', 'Caio'])
    assert len(eleicao.cedulas) == 1

def test_registrar_voto_rejeita_cedula_incompleta():
    eleicao = EleicaoAustralia(['Caio', 'Gi', 'Juh'], [])
    with pytest.raises(ValueError, match="ranquear exatamente todos os 3 candidatos"):
        eleicao.registrar_voto('eleitor1', ['Caio', 'Gi'])
    assert 'eleitor1' not in eleicao.votantes  # voto inválido não "gasta" o direito de voto

def test_registrar_voto_rejeita_candidato_falso_ou_duplicado():
    eleicao = EleicaoAustralia(['Caio', 'Gi'], [])
    with pytest.raises(ValueError, match="duplicados ou não registrados"):
        eleicao.registrar_voto('eleitor1', ['Caio', 'Caio'])
    with pytest.raises(ValueError, match="duplicados ou não registrados"):
        eleicao.registrar_voto('eleitor1', ['Caio', 'Fantasma'])

def test_registrar_voto_rejeita_voto_que_nao_e_lista():
    eleicao = EleicaoAustralia(['Caio', 'Gi'], [])
    with pytest.raises(TypeError, match="lista ordenada"):
        eleicao.registrar_voto('eleitor1', 'Caio')

def test_apuracao_com_votos_registrados_via_estado():
    eleicao = EleicaoAustralia(['Caio', 'Gi', 'Juh'], [])
    eleicao.iniciar_votacao()
    eleicao.apurar_voto('e1', ['Caio', 'Gi', 'Juh'])
    eleicao.apurar_voto('e2', ['Caio', 'Juh', 'Gi'])
    eleicao.apurar_voto('e3', ['Gi', 'Caio', 'Juh'])
    eleicao.encerrar_votacao()
    assert eleicao.apurar_vencedor() == 'Caio'
