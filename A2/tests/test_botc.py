import pytest

from src.botc import SistemaEleitoralBotC


def test_votos_insuficientes():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Alice", 4)
    assert sistema.apurar_vencedor() is None

def test_votos_suficientes_sucesso():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Alice", 5)
    assert sistema.apurar_vencedor() == "Alice"

def test_empate_na_maioria():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Alice", 6)
    sistema.registrar_votacao("Bob", 6)
    assert sistema.apurar_vencedor() is None

def test_maior_voto_vence():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Alice", 6)
    sistema.registrar_votacao("Bob", 8)
    assert sistema.apurar_vencedor() == "Bob"

def test_numero_vivos_invalido():
    with pytest.raises(ValueError, match="O número de jogadores vivos deve ser maior que zero."):
        SistemaEleitoralBotC(0)

def test_votos_negativos_invalido():
    sistema = SistemaEleitoralBotC(10)
    with pytest.raises(ValueError, match="O número de votos não pode ser negativo."):
        sistema.registrar_votacao("Alice", -1)

def test_votos_maior_numero_vivos_invalido():
    sistema = SistemaEleitoralBotC(10)
    with pytest.raises(ValueError, match="O número de votos não pode ser maior que a quantidade de jogadores."):
        sistema.registrar_votacao("Alice", 11)

def test_sem_votos():
    sistema = SistemaEleitoralBotC(10)
    assert sistema.apurar_vencedor() is None
