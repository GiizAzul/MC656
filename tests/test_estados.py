import pytest

from src.estados import AguardandoVotacao, EmVotacao, Encerrada
from src.interfaces import SistemaEleitoral


class SistemaEleitoralTeste(SistemaEleitoral):
    """Implementação concreta para testar o padrão State."""

    def __init__(self): # Inicializa o sistema de teste
        super().__init__()
        self.votos_registrados = []

    def apurar_vencedor(self): # define as funcoes obrigatorias
        return None

    def registrar_voto(self, eleitor_id, voto):
        self.votos_registrados.append((eleitor_id, voto))


def test_inicializacao_aguardando_votacao():
    sistema = SistemaEleitoralTeste() # cria instancia da classe de teste

    assert isinstance(sistema.estado, AguardandoVotacao) # instancia deve iniciar no estado AguardandoVotacao


def test_iniciar_votacao():
    sistema = SistemaEleitoralTeste()

    sistema.iniciar_votacao() # testa se a mudanca de estados ocorre corretamente 

    assert isinstance(sistema.estado, EmVotacao)


def test_apurar_voto():
    sistema = SistemaEleitoralTeste()
    sistema.iniciar_votacao()

    sistema.apurar_voto("aluno1", "SIM") # id e opcao de voto

    assert sistema.votos_registrados == [("aluno1", "SIM")] # verifica se a apuracao redireciona para a funcao registrar_voto


def test_voto_antes_iniciar():
    sistema = SistemaEleitoralTeste() # nao inicia a votacao

    with pytest.raises(RuntimeError): # verifica se aponta RuntimeError
        sistema.apurar_voto("aluno1", "SIM")


def test_encerrar_votacao():
    sistema = SistemaEleitoralTeste()
    sistema.iniciar_votacao()

    sistema.encerrar_votacao()

    assert isinstance(sistema.estado, Encerrada) # testa se a mudanca de estados ocorre corretamente 


def test_voto_apos_encerrar():
    sistema = SistemaEleitoralTeste()
    sistema.iniciar_votacao()
    sistema.encerrar_votacao() 

    with pytest.raises(RuntimeError): # verifica se aponta RuntimeError
        sistema.apurar_voto("aluno1", "SIM")