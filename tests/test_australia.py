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
    resultados = eleicao.apurar_resultados()
    assert resultados['vencedor'] == 'Samuel'
    assert len(resultados['rodadas']) == 1
    assert resultados['rodadas'][0]['eliminado'] is None

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


def test_aceita_cedula_com_permutacao_completa():
    candidatos = ['Caio', 'Gi', 'Juh']
    cedula = ['Juh', 'Caio', 'Gi']
    eleicao = EleicaoAustralia(candidatos, [cedula])
    assert eleicao.cedulas == [cedula]


def test_rejeita_cedula_com_candidatos_a_mais():
    """Uma cédula não pode conter mais nomes que o total de candidatos."""
    with pytest.raises(ValueError, match="ranquear exatamente todos os 2 candidatos"):
        EleicaoAustralia(['Caio', 'Gi'], [['Caio', 'Gi', 'Juh']])

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


def _eleicao_com_partidos():
    return EleicaoAustralia(
        ['A1', 'A2', 'B1'],
        [],
        partidos_candidatos={'Partido A': ['A1', 'A2'], 'Partido B': ['B1']},
    )


def test_configuracao_partidos_na_eleicao():
    assert _eleicao_com_partidos().partidos_candidatos['Partido A'] == ['A1', 'A2']
    from src.main import app
    assert app.state.eleicao_australia.partidos_candidatos['Partido Azul'] == ['Candidato A']


def test_configuracao_partidos_rejeita_associacoes_invalidas():
    """A associação deve cobrir candidatos oficiais uma única vez e ter partidos válidos."""
    candidatos = ['A1', 'A2', 'B1']
    casos_invalidos = [
        ({'Partido A': ['A1', 'A2'], 'Partido B': ['A2', 'B1']}, 'apenas um partido'),
        ({'Partido A': ['A1', 'A2'], 'Partido B': ['B1', 'Fantasma']}, 'não podem conter candidatos não registrados'),
        ({'Partido A': ['A1', 'A2']}, 'Todos os candidatos devem pertencer'),
        ({'Partido A': ['A1', 'A2'], '   ': ['B1']}, 'deve ter um nome'),
        ({'Partido A': ['A1', 'A2'], 'Partido B': []}, 'pelo menos um candidato'),
    ]

    for partidos, mensagem in casos_invalidos:
        with pytest.raises(ValueError, match=mensagem):
            EleicaoAustralia(candidatos, [], partidos_candidatos=partidos)


def test_converter_ranking_partidos_valida_e_expande_cedula():
    eleicao = _eleicao_com_partidos()
    assert eleicao.converter_ranking_partidos(['Partido B', 'Partido A']) == ['B1', 'A1', 'A2']


def test_converter_ranking_partidos_rejeita_entradas_invalidas():
    eleicao = _eleicao_com_partidos()
    with pytest.raises(TypeError, match='deve ser uma lista'):
        eleicao.converter_ranking_partidos('Partido A')

    casos_invalidos = [
        (['Partido A'], 'Faltam partidos'),
        (['Partido A', 'Partido A'], 'Partidos repetidos'),
        (['Partido A', 'Partido X'], 'Partidos não registrados'),
    ]
    for ranking, mensagem in casos_invalidos:
        with pytest.raises(ValueError, match=mensagem):
            eleicao.converter_ranking_partidos(ranking)

    sem_partidos = EleicaoAustralia(['A1'], [])
    with pytest.raises(ValueError, match='não está configurado'):
        sem_partidos.converter_ranking_partidos(['Partido A'])


def test_converter_posicoes_partidos_aceita_ranking_valido():
    eleicao = _eleicao_com_partidos()
    assert eleicao.converter_posicoes_partidos({'Partido A': '2', 'Partido B': 1}) == [
        'Partido B', 'Partido A'
    ]


def test_converter_posicoes_partidos_rejeita_ranking_invalido():
    eleicao = _eleicao_com_partidos()
    casos_invalidos = [
        ({'Partido A': 2}, 'Partidos sem posição.*Posições faltantes'),
        ({'Partido A': 1, 'Partido B': 1}, 'Posições repetidas.*Posições faltantes'),
        ({'Partido A': 1, 'Partido B': 3}, 'Posições faltantes.*fora do intervalo'),
        ({'Partido A': 'x', 'Partido B': 2}, 'Posições inválidas'),
        ({'Partido A': True, 'Partido B': 2}, 'Posições inválidas'),
        ({'Partido A': 1, 'Partido B': 2, 'Partido X': 3}, 'Partidos não registrados'),
    ]
    for posicoes, erro in casos_invalidos:
        with pytest.raises(ValueError, match=erro):
            eleicao.converter_posicoes_partidos(posicoes)

    with pytest.raises(TypeError, match='dicionário'):
        eleicao.converter_posicoes_partidos([1, 2])


def test_converter_posicoes_partidos_limites_intervalo():
    """Exercita os limites inclusivos 1 e N e os valores imediatamente externos."""
    eleicao = _eleicao_com_partidos()
    assert eleicao.converter_posicoes_partidos({'Partido A': 1, 'Partido B': 2}) == [
        'Partido A', 'Partido B'
    ]
    assert eleicao.converter_posicoes_partidos({'Partido A': 2, 'Partido B': 1}) == [
        'Partido B', 'Partido A'
    ]

    for posicao in (0, 3):
        with pytest.raises(ValueError, match='fora do intervalo'):
            eleicao.converter_posicoes_partidos({'Partido A': posicao, 'Partido B': 1})


def test_voto_por_partidos_respeita_estado_e_unicidade():
    eleicao = _eleicao_com_partidos()
    with pytest.raises(RuntimeError, match='ciclo de votação ativo'):
        eleicao.apurar_voto_partidos('eleitor', ['Partido A', 'Partido B'])
    with pytest.raises(RuntimeError, match='ciclo de votação ativo'):
        eleicao.apurar_voto_partidos_por_posicao('eleitor', {'Partido A': 1, 'Partido B': 2})

    eleicao.iniciar_votacao()
    eleicao.apurar_voto_partidos('eleitor', ['Partido A', 'Partido B'])
    assert eleicao.cedulas == [['A1', 'A2', 'B1']]
    with pytest.raises(ValueError, match='já registrou seu voto'):
        eleicao.apurar_voto_partidos('eleitor', ['Partido A', 'Partido B'])

    outra_eleicao = _eleicao_com_partidos()
    outra_eleicao.iniciar_votacao()
    outra_eleicao.apurar_voto_partidos_por_posicao(
        'eleitor-posicao', {'Partido A': 2, 'Partido B': 1}
    )
    assert outra_eleicao.cedulas == [['B1', 'A1', 'A2']]


def test_vitoria_na_contagem_inicial_sem_rodadas_adicionais():
    """Cobre o caso em que o vencedor atinge maioria absoluta na contagem inicial,
    garantindo que não sejam geradas rodadas subsequentes de eliminação."""
    candidatos = ['Candidato A', 'Candidato B', 'Candidato C']
    cedulas = [
        ['Candidato C', 'Candidato B', 'Candidato A'],
        ['Candidato A', 'Candidato B', 'Candidato C'],
        ['Candidato A', 'Candidato B', 'Candidato C'],
    ]
    eleicao = EleicaoAustralia(candidatos, cedulas)
    resultados = eleicao.apurar_resultados()
    assert resultados['vencedor'] == 'Candidato A'
    assert len(resultados['rodadas']) == 1
    assert resultados['rodadas'][0]['eliminado'] is None
    assert resultados['rodadas'][0]['contagem'] == {
        'Candidato A': 2,
        'Candidato B': 0,
        'Candidato C': 1,
    }
    assert resultados['rodadas'][0]['total'] == 3


def test_apuracao_multiplas_rodadas_quando_sem_maioria_inicial():
    """Garante que quando não há maioria na 1ª rodada, o candidato menos votado é
    eliminado e a contagem continua na rodada seguinte até a maioria ser atingida."""
    candidatos = ['Caio', 'Gi', 'Samuel']
    cedulas = [
        ['Caio', 'Samuel', 'Gi'],
        ['Caio', 'Samuel', 'Gi'],
        ['Samuel', 'Gi', 'Caio'],
        ['Gi', 'Samuel', 'Caio'],
        ['Gi', 'Samuel', 'Caio'],
    ]
    eleicao = EleicaoAustralia(candidatos, cedulas)
    resultados = eleicao.apurar_resultados()
    assert resultados['vencedor'] == 'Gi'
    assert len(resultados['rodadas']) == 2
    assert resultados['rodadas'][0]['eliminado'] == 'Samuel'
    assert resultados['rodadas'][0]['contagem'] == {'Caio': 2, 'Gi': 2, 'Samuel': 1}
    assert resultados['rodadas'][1]['eliminado'] is None
    assert resultados['rodadas'][1]['contagem'] == {'Caio': 2, 'Gi': 3}


def test_apuracao_um_candidato():
    eleicao = EleicaoAustralia(['Samuel'], [['Samuel']])
    resultados = eleicao.apurar_resultados()
    assert resultados['vencedor'] == 'Samuel'
    assert len(resultados['rodadas']) == 1
    assert resultados['rodadas'][0]['contagem'] == {'Samuel': 1}

