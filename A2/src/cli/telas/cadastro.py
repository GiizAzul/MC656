from enum import Enum
from getpass import getpass

from src.autenticacao import (
    CandidatoAustralia,
    EleitorAustralia,
    EstudanteCACo,
    GestaoCACo,
    JogadorBOTC,
    ServicoAutenticacao,
    StoryTellerBOTC,
)

from src.autenticacao.base import Usuario
from src.cli import cli_utils


class TipoConta(Enum):
    """Tipos de conta que podem ser criados, um por escopo já existente."""

    CACO_ESTUDANTE = "1"
    CACO_GESTAO = "2"
    AUSTRALIA_ELEITOR = "3"
    AUSTRALIA_CANDIDATO = "4"
    BOTC_JOGADOR = "5"
    BOTC_STORYTELLER = "6"


_NOMES_TIPO = {
    TipoConta.CACO_ESTUDANTE: "Estudante (CACo)",
    TipoConta.CACO_GESTAO: "Gestão (CACo)",
    TipoConta.AUSTRALIA_ELEITOR: "Eleitor (Eleição Austrália)",
    TipoConta.AUSTRALIA_CANDIDATO: "Candidato (Eleição Austrália)",
    TipoConta.BOTC_JOGADOR: "Jogador (Blood on the Clocktower)",
    TipoConta.BOTC_STORYTELLER: "StoryTeller (Blood on the Clocktower)",
}


def decidir_tipo(escolha: str) -> TipoConta | None:
    """Decide qual tipo de conta foi escolhido a partir da entrada do usuário."""
    valores_validos = [tipo.value for tipo in TipoConta]
    chave = cli_utils.decidir_por_chave(escolha, valores_validos)
    return TipoConta(chave) if chave is not None else None


def construir_usuario(
    tipo: TipoConta,
    id_: int,
    username: str,
    senha: str,
    nome_real: str,
    ra: int | None = None,
) -> Usuario:
    """Instancia a subclasse de `Usuario` correspondente ao tipo escolhido."""
    if tipo == TipoConta.CACO_ESTUDANTE:
        if ra is None:
            raise ValueError("RA é obrigatório para contas de estudante do CACo.")
        return EstudanteCACo(id_, username, senha, nome_real, ra)
    if tipo == TipoConta.CACO_GESTAO:
        return GestaoCACo(id_, username, senha, nome_real)
    if tipo == TipoConta.AUSTRALIA_ELEITOR:
        return EleitorAustralia(id_, username, senha, nome_real)
    if tipo == TipoConta.AUSTRALIA_CANDIDATO:
        return CandidatoAustralia(id_, username, senha, nome_real)
    if tipo == TipoConta.BOTC_JOGADOR:
        return JogadorBOTC(id_, username, senha, nome_real)
    return StoryTellerBOTC(id_, username, senha, nome_real)


def tela_cadastro(servico: ServicoAutenticacao, proximo_id: int) -> Usuario | None:
    """Cria uma nova conta: escolhe o tipo, coleta os dados e registra."""
    cli_utils.imprimir_titulo("Criar conta")
    cli_utils.imprimir_menu([(tipo.value, _NOMES_TIPO[tipo]) for tipo in TipoConta])

    tipo = decidir_tipo(input("Tipo de conta: "))
    if tipo is None:
        cli_utils.imprimir_erro("Tipo de conta inválido.")
        return None

    username = input("Novo usuário: ")

    while True:
        senha = getpass("Nova senha: ")
        senha_confirma = getpass("Confirme a senha: ")

        if not senha:
            cli_utils.imprimir_erro("A senha não pode ser vazia.")
            continue

        if senha != senha_confirma:
            cli_utils.imprimir_erro("Senhas não batem.")
            continue

        break

    nome_real = input("Nome completo: ")

    ra = None
    if tipo == TipoConta.CACO_ESTUDANTE:
        try:
            ra = int(input("RA: ").strip())
        except ValueError:
            cli_utils.imprimir_erro("RA inválido: deve ser um número.")
            return None

        if not 100000 <= ra <= 999999:
            cli_utils.imprimir_erro("RA inválido: deve ter 6 dígitos.")
            return None

    novo_usuario = construir_usuario(tipo, proximo_id, username, senha, nome_real, ra)

    try:
        servico.registrar(novo_usuario)
    except ValueError as erro:
        cli_utils.imprimir_erro(str(erro))
        return None

    cli_utils.imprimir_sucesso(f"Conta criada com sucesso! Bem-vindo(a), {nome_real}.")
    return novo_usuario
