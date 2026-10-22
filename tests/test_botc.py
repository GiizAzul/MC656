import pytest

from src.botc import (
    JogadorBotC,
    ModificadorMultiplicador,
    ModificadorNegativo,
    ModificadorNulo,
    SistemaEleitoralBotC,
    StatusJogador,
    VotoPadrao,
)

# ==============================================================================
# Testes Legados de Apuração da Forca (Issue #69)
# ==============================================================================

def test_votos_insuficientes():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Gi", 4)
    assert sistema.apurar_vencedor() is None


def test_votos_suficientes_sucesso():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Gi", 5)
    assert sistema.apurar_vencedor() == "Gi"


def test_empate_na_maioria():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Gi", 6)
    sistema.registrar_votacao("Caio Lima", 6)
    assert sistema.apurar_vencedor() is None


def test_maior_voto_vence():
    sistema = SistemaEleitoralBotC(10)
    sistema.registrar_votacao("Gi", 6)
    sistema.registrar_votacao("Caio Lima", 8)
    assert sistema.apurar_vencedor() == "Caio Lima"


def test_numero_vivos_invalido():
    with pytest.raises(ValueError, match="O número de jogadores vivos deve ser maior que zero."):
        SistemaEleitoralBotC(0)


def test_votos_negativos_invalido():
    sistema = SistemaEleitoralBotC(10)
    with pytest.raises(ValueError, match="O número de votos não pode ser negativo."):
        sistema.registrar_votacao("Gi", -1)


def test_votos_maior_numero_vivos_invalido():
    sistema = SistemaEleitoralBotC(10)
    with pytest.raises(ValueError, match="O número de votos não pode ser maior que a quantidade de jogadores."):
        sistema.registrar_votacao("Gi", 11)


def test_sem_votos():
    sistema = SistemaEleitoralBotC(10)
    assert sistema.apurar_vencedor() is None


def test_id_candidato_invalido():
    """Garante que o sistema barre candidatos sem User_ID válido."""
    sistema = SistemaEleitoralBotC(10)
    with pytest.raises(ValueError, match="O identificador do candidato deve ser um User_ID válido."):
        sistema.registrar_votacao("", 5)

    with pytest.raises(ValueError, match="O identificador do candidato deve ser um User_ID válido."):
        sistema.registrar_votacao(None, 5)


# ==============================================================================
# Testes da Issue #71: Controle de Status de Vida e Voto Fantasma
# ==============================================================================

def test_jogador_validacao_inicial():
    with pytest.raises(ValueError, match="O identificador do jogador deve ser um User_ID válido."):
        JogadorBotC("", "Leo")

    with pytest.raises(ValueError, match="O identificador do jogador deve ser um User_ID válido."):
        JogadorBotC(None, "Leo")

    with pytest.raises(ValueError, match="O nome do jogador deve ser um texto válido."):
        JogadorBotC("j1", "")


def test_jogador_vivo_pode_votar_sempre():
    jogador = JogadorBotC("j1", "Leo", StatusJogador.VIVO)
    assert jogador.pode_votar() is True
    # Consumir voto fantasma em vivo não tem efeito
    assert jogador.consumir_voto_fantasma() is False
    assert jogador.status == StatusJogador.VIVO
    assert jogador.pode_votar() is True


def test_jogador_morto_com_fantasma_consome_voto():
    jogador = JogadorBotC("j2", "Julia", StatusJogador.MORTO_COM_FANTASMA)
    assert jogador.pode_votar() is True

    # Ao votar, consome o voto fantasma e transita para MORTO_SEM_FANTASMA
    consumiu = jogador.consumir_voto_fantasma()
    assert consumiu is True
    assert jogador.status == StatusJogador.MORTO_SEM_FANTASMA
    assert jogador.pode_votar() is False

    # Segunda tentativa não consome nada
    assert jogador.consumir_voto_fantasma() is False


def test_sistema_bloqueia_voto_morto_sem_fantasma():
    j_vivo = JogadorBotC("v1", "Vivo 1", StatusJogador.VIVO)
    j_morto_sem_voto = JogadorBotC("m1", "Morto Sem Voto", StatusJogador.MORTO_SEM_FANTASMA)
    sistema = SistemaEleitoralBotC(jogadores=[j_vivo, j_morto_sem_voto])

    with pytest.raises(ValueError, match="está morto e não possui mais voto fantasma"):
        sistema.registrar_voto_jogador("candidato_x", "m1")


def test_sistema_consome_voto_fantasma_automaticamente():
    j_vivo = JogadorBotC("v1", "Vivo 1", StatusJogador.VIVO)
    j_fantasma = JogadorBotC("m2", "Morto Com Voto", StatusJogador.MORTO_COM_FANTASMA)
    sistema = SistemaEleitoralBotC(jogadores=[j_vivo, j_fantasma])

    # Primeiro voto do fantasma: válido e contabiliza
    peso = sistema.registrar_voto_jogador("candidato_x", "m2")
    assert peso == 1
    assert j_fantasma.status == StatusJogador.MORTO_SEM_FANTASMA

    # Tentativa de votar novamente para outro candidato na mesma rodada/jogo: bloqueado
    with pytest.raises(ValueError, match="está morto e não possui mais voto fantasma"):
        sistema.registrar_voto_jogador("candidato_y", "m2")


def test_bloqueio_voto_duplo_mesma_nomeacao():
    j_vivo = JogadorBotC("v1", "Vivo 1", StatusJogador.VIVO)
    sistema = SistemaEleitoralBotC(jogadores=[j_vivo])

    sistema.registrar_voto_jogador("candidato_x", "v1")
    with pytest.raises(ValueError, match="já votou nesta nomeação"):
        sistema.registrar_voto_jogador("candidato_x", "v1")


# ==============================================================================
# Testes da Issue #70: Padrão Decorator e Modificadores de Voto
# ==============================================================================

def test_decorator_voto_padrao():
    voto = VotoPadrao()
    assert voto.calcular_peso() == 1


def test_decorator_multiplicador():
    voto = VotoPadrao()
    voto_triplo = ModificadorMultiplicador(voto, fator=3)
    assert voto_triplo.calcular_peso() == 3
    assert voto_triplo.componente is voto


def test_decorator_multiplicador_fator_invalido():
    voto = VotoPadrao()
    with pytest.raises(ValueError, match="fator de multiplicação deve ser maior que zero"):
        ModificadorMultiplicador(voto, fator=0)


def test_decorator_negativo():
    voto = VotoPadrao()
    voto_negativo = ModificadorNegativo(voto)
    assert voto_negativo.calcular_peso() == -1


def test_decorator_multiplicador_com_negativador_resulta_menos_tres():
    """
    Verifica a regra de negócio específica:
    O negativador combinado ao multiplicador x3 resulta em -3.
    """
    voto_base = VotoPadrao()
    voto_multiplicado = ModificadorMultiplicador(voto_base, fator=3)
    voto_negativado = ModificadorNegativo(voto_multiplicado)
    assert voto_negativado.calcular_peso() == -3

    # Ordem inversa de decoração também deve resultar em -3
    voto_negativo_primeiro = ModificadorNegativo(voto_base)
    voto_multiplicado_depois = ModificadorMultiplicador(voto_negativo_primeiro, fator=3)
    assert voto_multiplicado_depois.calcular_peso() == -3


def test_decorator_nulo():
    voto = VotoPadrao()
    voto_nulo = ModificadorNulo(voto)
    assert voto_nulo.calcular_peso() == 0

    # Voto nulo mesmo com multiplicador ou negativador permanece 0
    assert ModificadorMultiplicador(voto_nulo, fator=3).calcular_peso() == 0
    assert ModificadorNegativo(voto_nulo).calcular_peso() == 0


def test_decorador_componente_nulo_invalido():
    with pytest.raises(ValueError, match="componente de voto a ser decorado não pode ser nulo"):
        ModificadorMultiplicador(None)


def test_decorador_base_delegacao_direta():
    """Garante que a classe base do Decorador repasse a chamada de cálculo por delegação."""
    from src.botc import DecoradorModificadorVoto
    voto_base = VotoPadrao(valor=2)
    decorador_base = DecoradorModificadorVoto(voto_base)
    assert decorador_base.calcular_peso() == 2
    assert decorador_base.componente is voto_base


def test_jogador_modificadores_helpers():
    jogador = JogadorBotC("j1", "Leo")
    assert jogador.calcular_peso_voto() == 1

    jogador.adicionar_multiplicador(3)
    assert jogador.calcular_peso_voto() == 3

    jogador.adicionar_negativador()
    assert jogador.calcular_peso_voto() == -3

    jogador.resetar_modificador()
    assert jogador.calcular_peso_voto() == 1

    jogador.anular_voto()
    assert jogador.calcular_peso_voto() == 0


# ==============================================================================
# Testes de Integração do Sistema Eleitoral com Voto Fantasma e Modificadores
# ==============================================================================

def test_apuracao_com_modificador_multiplicador():
    """Demonstra que modificador x3 pode garantir maioria com menos votantes."""
    # 6 jogadores vivos -> maioria precisa de 6 / 2 = 3 votos
    jogadores = [JogadorBotC(f"j{i}", f"Jogador {i}", StatusJogador.VIVO) for i in range(1, 7)]
    sistema = SistemaEleitoralBotC(jogadores=jogadores)

    # j1 tem modificador x3
    sistema.aplicar_modificador("j1", ModificadorMultiplicador(VotoPadrao(), fator=3))

    # Apenas j1 vota no candidato_a -> deve somar 3 votos e atingir a maioria (3 >= 3.0)
    sistema.registrar_voto_jogador("candidato_a", "j1")
    assert sistema.votos["candidato_a"] == 3
    assert sistema.apurar_vencedor() == "candidato_a"


def test_apuracao_com_modificador_negativador_impede_forca():
    """Demonstra que voto negativado reduz a contagem e impede a forca."""
    # 6 jogadores vivos -> maioria = 3.0
    jogadores = [JogadorBotC(f"j{i}", f"Jogador {i}", StatusJogador.VIVO) for i in range(1, 7)]
    sistema = SistemaEleitoralBotC(jogadores=jogadores)

    # j1 e j2 são votos normais (+1 cada)
    sistema.registrar_voto_jogador("candidato_b", "j1")
    sistema.registrar_voto_jogador("candidato_b", "j2")

    # j3 tem voto triplo negativado (-3)
    sistema.obter_jogador("j3").adicionar_multiplicador(3)
    sistema.obter_jogador("j3").adicionar_negativador()
    sistema.registrar_voto_jogador("candidato_b", "j3")

    # Total de votos: 1 + 1 - 3 = -1 (insuficiente para atingir a maioria de 3.0)
    assert sistema.votos["candidato_b"] == -1
    assert sistema.apurar_vencedor() is None


def test_apuracao_com_voto_fantasma_desempata():
    """Demonstra que um jogador morto pode usar seu voto fantasma para desempatar."""
    # 4 vivos (maioria = 2.0) e 1 morto com voto fantasma
    jogadores = [
        JogadorBotC("v1", "Vivo 1", StatusJogador.VIVO),
        JogadorBotC("v2", "Vivo 2", StatusJogador.VIVO),
        JogadorBotC("v3", "Vivo 3", StatusJogador.VIVO),
        JogadorBotC("v4", "Vivo 4", StatusJogador.VIVO),
        JogadorBotC("m1", "Morto 1", StatusJogador.MORTO_COM_FANTASMA),
    ]
    sistema = SistemaEleitoralBotC(jogadores=jogadores)

    # Candidato A recebe votos de v1 e v2 (2 votos)
    sistema.registrar_voto_jogador("candidato_a", "v1")
    sistema.registrar_voto_jogador("candidato_a", "v2")

    # Candidato B recebe votos de v3 e v4 (2 votos)
    sistema.registrar_voto_jogador("candidato_b", "v3")
    sistema.registrar_voto_jogador("candidato_b", "v4")

    # No momento, empate em 2 votos (ninguém é executado)
    assert sistema.apurar_vencedor() is None

    # Morto com voto fantasma vota no Candidato A -> Candidato A fica com 3 votos
    sistema.registrar_voto_jogador("candidato_a", "m1")
    assert sistema.votos["candidato_a"] == 3
    assert sistema.apurar_vencedor() == "candidato_a"
    assert sistema.obter_jogador("m1").status == StatusJogador.MORTO_SEM_FANTASMA


def test_metodos_auxiliares_sistema():
    sistema = SistemaEleitoralBotC(4)
    assert sistema.obter_jogador("inexistente") is None

    with pytest.raises(ValueError, match="não encontrado"):
        sistema.alterar_status_jogador("inexistente", StatusJogador.VIVO)

    with pytest.raises(ValueError, match="não encontrado"):
        sistema.aplicar_modificador("inexistente", VotoPadrao())

    with pytest.raises(TypeError, match="Instância de jogador inválida"):
        sistema.adicionar_jogador("não é JogadorBotC")

    with pytest.raises(ValueError, match="lista de jogadores não pode ser vazia"):
        SistemaEleitoralBotC(jogadores=[])

    with pytest.raises(ValueError, match="É necessário informar o número de jogadores vivos"):
        SistemaEleitoralBotC()

    # Testando setter de jogadores vivos
    sistema.jogadores_vivos = 6
    assert sistema.jogadores_vivos == 6

    with pytest.raises(ValueError, match="maior que zero"):
        sistema.jogadores_vivos = 0


def test_registrar_votos_jogadores_multiplos():
    jogadores = [JogadorBotC(f"j{i}", f"Jogador {i}", StatusJogador.VIVO) for i in range(1, 4)]
    sistema = SistemaEleitoralBotC(jogadores=jogadores)
    total = sistema.registrar_votos_jogadores("cand_x", ["j1", "j2"])
    assert total == 2
    assert sistema.votos["cand_x"] == 2


def test_jogador_aplicar_modificador_nulo():
    jogador = JogadorBotC("j1", "Leo")
    with pytest.raises(ValueError, match="modificador não pode ser nulo"):
        jogador.aplicar_modificador(None)


def test_sistema_votante_e_candidato_validacoes_extras():
    sistema = SistemaEleitoralBotC(3)
    with pytest.raises(ValueError, match="Votante 'nao_existe' não encontrado"):
        sistema.registrar_voto_jogador("cand", "nao_existe")
    with pytest.raises(ValueError, match="identificador do candidato deve ser um User_ID válido"):
        sistema.registrar_voto_jogador("", "jogador_1")
