def imprimir_titulo(titulo: str) -> None:
    """Imprime um titulo padronizado para uma tela."""
    print(f"\n=== {titulo} ===")


def imprimir_mensagem(mensagem: str) -> None:
    """Imprime uma mensagem informativa."""
    print(mensagem)


def imprimir_erro(mensagem: str) -> None:
    """Imprime uma mensagem de erro."""
    print(f"[ERRO] {mensagem}")


def imprimir_sucesso(mensagem: str) -> None:
    """Imprime uma mensagem de operacao realizada com sucesso."""
    print(f"[OK] {mensagem}")


def imprimir_menu(opcoes: list[tuple[str, str]]) -> None:
    """Imprime uma lista de opções no formato '[chave] descrição'."""
    for chave, descricao in opcoes:
        print(f"  [{chave}] {descricao}")


def decidir_por_chave(escolha: str, opcoes_validas: list[str]) -> str | None:
    """Função pura de decisão usada pelas telas para interpretar um menu."""
    escolha_normalizada = escolha.strip()
    if escolha_normalizada in opcoes_validas:
        return escolha_normalizada
    return None
