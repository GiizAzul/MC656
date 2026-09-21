from src.autenticacao import (
    CandidatoAustralia,
    EleitorAustralia,
    EstudanteCACo,
    GestaoCACo,
    JogadorBOTC,
    ServicoAutenticacao,
    StoryTellerBOTC,
)
from src.botc import SistemaEleitoralBotC
from src.caco import EleicaoAssembleia
from src.cli.app import executar_app
from src.cli.sessao import Sessao

def montar_servico_autenticacao() -> ServicoAutenticacao:
    """Cria e popula o serviço de autenticação com usuários de demonstração."""
    servico = ServicoAutenticacao()

    servico.registrar(GestaoCACo(1, "gestao_caco", "gestao123", "Diretoria do CACo"))
    servico.registrar(EstudanteCACo(2, "estudante1", "senha123", "Julia de Souza Nardo", ra=123456))

    servico.registrar(StoryTellerBOTC(3, "narrador", "narrador123", "Storyteller"))
    servico.registrar(JogadorBOTC(4, "jogador1", "senha123", "Leonardo"))

    servico.registrar(CandidatoAustralia(5, "candidato1", "senha123", "Carlos Candidato"))
    servico.registrar(EleitorAustralia(6, "eleitor1", "senha123", "Diego Eleitor"))

    return servico

def montar_sessao() -> Sessao:
    """Monta a sessão inicial com o estado de demonstração de cada contexto."""
    alunos_cadastrados = [
        "estudante1", "Aluno2", "Aluno3", "Aluno4", "Aluno5",
        "Aluno6", "Aluno7", "Aluno8", "Aluno9", "Aluno10",
    ]
    eleitores_presentes = ["estudante1", "Aluno2", "Aluno3"]

    eleicao_caco = EleicaoAssembleia(
        alunos_cadastrados=alunos_cadastrados,
        eleitores=eleitores_presentes,
        duracao_ciclo=120.0,
    )

    candidatos_australia = ["Carlos Candidato", "Outro Candidato"]

    sistema_botc = SistemaEleitoralBotC(jogadores_vivos=5)

    return Sessao(
        eleicao_caco=eleicao_caco,
        candidatos_australia=candidatos_australia,
        sistema_botc=sistema_botc,
    )

def main() -> None:
    """Monta as dependências e inicia o loop principal do CLI."""
    servico_auth = montar_servico_autenticacao()
    sessao = montar_sessao()
    executar_app(servico_auth, sessao)


if __name__ == "__main__":
    main()
