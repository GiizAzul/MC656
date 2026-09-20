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
    with pytest.raises(ValueError):
        SistemaEleitoralBotC(0)

def test_votos_negativos_invalido():
    sistema = SistemaEleitoralBotC(10)
    with pytest.raises(ValueError):
        sistema.registrar_votacao("Alice", -1)

def test_sem_votos():
    sistema = SistemaEleitoralBotC(10)
    assert sistema.apurar_vencedor() is None
