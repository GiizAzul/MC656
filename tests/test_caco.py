import time

import pytest

from src import EleicaoAssembleia
from src.caco import OpcaoVoto


# Verifica se está barrando corretamente não alunos
def test_eleitor_nao_aluno():
    alunos = [
        'Juh', 'Samuel', 'Gi', 'Caio', 'Leo',
        'Ana', 'Carol', 'Leticia', 'Naomi', 'Estrela'
    ]

    eleitores = [
         'Juh', 'Samuel', 'Gi', 'Caio', 'Leo', 'PessoaFalsa'
    ]

    with pytest.raises(
        ValueError,
        match="O eleitor 'PessoaFalsa' não está cadastrado como aluno."
    ):
        EleicaoAssembleia(alunos, eleitores, 60)


# Verifica se está barrando quórum não suficiente
def test_abaixo_quorum_minimo():

    # quorum mínimo == 1 
    alunos = [
        'Juh', 'Samuel', 'Gi', 'Caio', 'Leo',
        'Ana', 'Carol', 'Leticia', 'Naomi', 'Estrela'
    ]

    eleitores = []

    with pytest.raises(
        RuntimeError,
        match="Quórum mínimo não foi satisfeito"
    ):
        EleicaoAssembleia(alunos, eleitores, 60)

# Verifica se passa quórum suficiente
def test_quorum_minimo():

    # quorum mínimo == 1 (teto)
    alunos = [
        'Juh', 'Samuel', 'Gi', 'Caio', 'Leo',
        'Ana', 'Carol', 'Leticia', 'Naomi'
    ]

    eleitores = ['Juh']

    eleicao = EleicaoAssembleia(alunos, eleitores, 60)
    assert eleicao is not None


# Verifica se está barrando duracão inválida
def test_duracao_invalida():
    alunos = [
        'Juh', 'Samuel', 'Gi', 'Caio', 'Leo',
        'Ana', 'Carol', 'Leticia', 'Naomi', 'Estrela'
    ]

    eleitores = [
        'Juh', 'Samuel', 'Gi', 'Caio', 'Leo'
    ]

    with pytest.raises(
        ValueError,
        match="A duração do ciclo deve ser maior que zero."
    ):
        EleicaoAssembleia(alunos, eleitores, 0)


# Cria eleicão teste
def criar_eleicao():
    alunos = [
        'Juh', 'Samuel', 'Gi', 'Caio', 'Leo',
        'Ana', 'Carol', 'Leticia', 'Naomi', 'Estrela'
    ]

    eleitores = [
        'Juh', 'Samuel', 'Gi', 'Caio', 'Leo'
    ]

    return EleicaoAssembleia(alunos, eleitores, 30)

# Testa vitoria quando APROVAR possui mais de 50% dos votos não nulos
def test_vitoria_aprovacao():

    eleicao = criar_eleicao()
    eleicao.iniciar_votacao()

    eleicao.registrar_voto('Juh', OpcaoVoto.APROVAR)
    eleicao.registrar_voto('Samuel', OpcaoVoto.APROVAR)
    eleicao.registrar_voto('Gi', OpcaoVoto.APROVAR)
    eleicao.registrar_voto('Caio', OpcaoVoto.REJEITAR)
    eleicao.registrar_voto('Leo', OpcaoVoto.ABSTER)

    eleicao.encerrar_votacao()

    assert eleicao.apurar_vencedor() == 'APROVADA'


# Testa vitoria quando REJEITAR possui mais de 50% dos votos não nulos
def test_vitoria_rejeicao():

    eleicao = criar_eleicao()
    eleicao.iniciar_votacao()

    eleicao.registrar_voto('Juh', OpcaoVoto.REJEITAR)
    eleicao.registrar_voto('Samuel', OpcaoVoto.REJEITAR)
    eleicao.registrar_voto('Gi', OpcaoVoto.REJEITAR)
    eleicao.registrar_voto('Caio', OpcaoVoto.ABSTER)
    eleicao.registrar_voto('Leo', OpcaoVoto.APROVAR)

    eleicao.encerrar_votacao()

    assert eleicao.apurar_vencedor() == 'VETADA'


# Testa empate em APROVAR e REJEITAR
def test_empate():
    
    eleicao = criar_eleicao()
    eleicao.iniciar_votacao()

    eleicao.registrar_voto('Juh', OpcaoVoto.REJEITAR)
    eleicao.registrar_voto('Samuel', OpcaoVoto.REJEITAR)
    eleicao.registrar_voto('Gi', OpcaoVoto.APROVAR)
    eleicao.registrar_voto('Caio', OpcaoVoto.APROVAR)
    eleicao.registrar_voto('Leo', OpcaoVoto.ABSTER)

    eleicao.encerrar_votacao()

    assert eleicao.apurar_vencedor() == 'VETADA'

# Testa abstencão total
def test_todos_abstiveram():
    eleicao = criar_eleicao()
    eleicao.iniciar_votacao()

    eleicao.registrar_voto('Juh', OpcaoVoto.ABSTER)
    eleicao.registrar_voto('Samuel', OpcaoVoto.ABSTER)
    eleicao.registrar_voto('Gi', OpcaoVoto.ABSTER)
    eleicao.registrar_voto('Caio', OpcaoVoto.ABSTER)
    eleicao.registrar_voto('Leo', OpcaoVoto.ABSTER)

    eleicao.encerrar_votacao()

    assert eleicao.apurar_vencedor() == 'VETADA'

# Testa se barra corretamente multiplos votos
def test_voto_unico():

    eleicao = criar_eleicao()
    eleicao.iniciar_votacao()

    eleicao.registrar_voto('Juh', OpcaoVoto.APROVAR)

    with pytest.raises(
        ValueError,
        match="O eleitor já registrou um voto nesta votação."
    ):
        eleicao.registrar_voto('Juh', OpcaoVoto.REJEITAR)


# Testa se barra votos antes do ínico da votacão
def test_voto_antes_do_inicio():

    eleicao = criar_eleicao()

    with pytest.raises(
        RuntimeError,
        match="Não existe um ciclo de votação ativo."
    ):
        eleicao.registrar_voto('Juh', OpcaoVoto.APROVAR)

# Testa se barra votos depois do fim da votacão
def test_voto_depois_do_encerramento():

    eleicao = criar_eleicao()
    eleicao.iniciar_votacao()
    eleicao.encerrar_votacao()

    with pytest.raises(
        RuntimeError,
        match="Não existe um ciclo de votação ativo."
    ):
        eleicao.registrar_voto('Juh', OpcaoVoto.APROVAR)

# Testa se uma votação não pode ser iniciada duas vezes
def test_iniciar_votacao_duplicado():

    eleicao = criar_eleicao()

    eleicao.iniciar_votacao()

    with pytest.raises(
        RuntimeError,
        match="A votação já está em andamento."
    ):
        eleicao.iniciar_votacao()

# Testa se uma votação não pode ser reaberta após encerramento
def test_reiniciar_votacao_encerrada():

    eleicao = criar_eleicao()

    eleicao.iniciar_votacao()
    eleicao.encerrar_votacao()

    with pytest.raises(
        RuntimeError,
        match="A votação já foi encerrada."
    ):
        eleicao.iniciar_votacao()

# Testa se os contadores registram corretamente cada tipo de voto
def test_contagem_dos_votos():
    """Testa se os contadores registram corretamente cada tipo de voto."""
    eleicao = criar_eleicao()
    eleicao.iniciar_votacao()

    eleicao.registrar_voto('Juh', OpcaoVoto.APROVAR)
    eleicao.registrar_voto('Samuel', OpcaoVoto.APROVAR)
    eleicao.registrar_voto('Caio', OpcaoVoto.REJEITAR)
    eleicao.registrar_voto('Gi', OpcaoVoto.ABSTER)
    eleicao.registrar_voto('Leo', OpcaoVoto.ABSTER)

    contadores = eleicao.obter_contadores()

    assert contadores['APROVAR'] == 2
    assert contadores['REJEITAR'] == 1
    assert contadores['ABSTER'] == 2

# Testa se o fim do tempo é identificado corretamente 
def test_tempo_acabou():
    
    eleicao = EleicaoAssembleia(
        ['Juh', 'Samuel', 'Gi', 'Caio', 'Leo'],
        ['Juh', 'Samuel', 'Gi', 'Caio', 'Leo'],
        0.1
    )

    eleicao.iniciar_votacao()

    # deve retornar falso logo após iniciar
    assert eleicao.tempo_acabou() is False

    time.sleep(0.2)

    # deve retornar verdadeiro ao fim do tempo
    assert eleicao.tempo_acabou() is True
