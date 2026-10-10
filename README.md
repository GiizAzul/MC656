# MC656

Repositório para o projeto da disciplina MC656 – Engenharia de Software

## Membros

|Name|RA|
|-|-|
|Giovana Jacome Marchetti|177700|
|Caio Lima Albuquerque|288808|
|Samuel Rodrigues Ferreira|195440|
|Julia de Souza Nardo|281272|
|Leonardo Carvalho De Luca|288820|

## Sobre o projeto

O projeto simula um sistema de votação capaz de operar em três contextos
eleitorais diferentes, cada um com suas próprias regras de apuração e perfis
de usuário:

- **Assembleia do CACo** — votação de pauta por Aprovar / Rejeitar / Abster-se,
  com quórum mínimo de eleitores e um ciclo de votação com duração definida.
- **Eleição da Austrália** — voto único transferível (ranking de candidatos, com
  eliminação e transferência de votos por rodadas até haver maioria absoluta).
- **Blood on the Clocktower** — votação de execução, em que um jogador nomeado   precisa de votos maiores ou iguais à metade dos jogadores vivos para ser  executado.

## Organização do repositório

O repositório reúne o código da aplicação (na raiz) e a documentação das
atividades da disciplina (em `docs/`):

- **Raiz (`main.py`, `src/`, `tests/`)** — o projeto descrito neste README
  (Atividade 2): código-fonte, testes e o ponto de entrada da aplicação.
- **`docs/A1_report/`** — relatório da Atividade 1 (LaTeX e PDF) com a definição
  do processo de desenvolvimento, incluindo diagramas (casos de uso, domínio,
  processo) e protótipos de telas.
- **`docs/A3_report/`** — relatório da Atividade 3 (LaTeX): elicitação e análise
  de requisitos, épicos, histórias de usuário e backlog priorizado. **Em
  andamento.**
- **`.github/workflows/ci.yml`** — pipeline de integração contínua (ver
  [Integração contínua](#integração-contínua)).

As seções abaixo (estrutura, como rodar, testes) se referem ao conteúdo da
pasta `A2/`.

## Estrutura do projeto

> ⚠️ **Status: prévia inicial.** Esta versão cobre a lógica central dos três
> contextos e uma interface de linha de comando (CLI) para navegar por ela.
> Veja [Status do projeto e próximos passos](#status-do-projeto-e-próximos-passos).

```
.
├── main.py                        # ponto de entrada da aplicação
├── requirements.txt               # dependências de teste/lint
├── src/
│   ├── caco.py                    # motor da Assembleia do CACo
│   ├── australia.py               # motor da Eleição Austrália (voto transferível)
│   ├── botc.py                    # motor do Blood on the Clocktower
│   ├── interfaces.py              # interface comum aos motores de votação
│   ├── autenticacao/              # usuários, perfis (escopos) e serviço de login
│   └── cli/                       # loop principal e telas do terminal
│       ├── app.py                 
│       ├── sessao.py              
│       ├── cli_utils.py
│       └── telas/                 # uma tela por fluxo (login, cadastro, cada contexto, etc.)
├── tests/                         # testes automatizados (pytest) de domínio, autenticação e interface
├── docs/
│   ├── A1_report/                 # Atividade 1: processo de desenvolvimento
│   └── A3_report/                 # Atividade 3: requisitos
└── .github/workflows/ci.yml       # CI: build, lint (ruff) e testes (pytest + cobertura)
```

## Requisitos

- Python 3.10 ou superior.
- Não há dependências externas para rodar a aplicação. O `requirements.txt` lista somente ferramentas de desenvolvimento (testes e lint).

## Como rodar

A partir da raiz do repositório:

```bash
python3 main.py
```


Ao iniciar, é possível **criar uma conta nova** ou **entrar** com um dos
usuários de demonstração já cadastrados em `main.py`:

| Usuário       | Senha         | Perfil                          |
|---------------|---------------|----------------------------------|
| `gestao_caco` | `gestao123`   | Gestão do CACo                  |
| `estudante1`  | `senha123`    | Estudante do CACo                |
| `narrador`    | `narrador123` | Storyteller (BotC)                |
| `jogador1`    | `senha123`    | Jogador (BotC)                   |
| `candidato1`  | `senha123`    | Candidato (Eleição Austrália)     |
| `eleitor1`    | `senha123`    | Eleitor (Eleição Austrália)       |

## Como rodar os testes

Também a partir da raiz do repositório:


## Como rodar os testes

Também a partir da raiz do repositório:

```bash
pip install -r requirements.txt
pytest
```

Para ver a cobertura de testes (como na CI):

```bash
pytest --cov=src --cov-report=term
```

Para checar o estilo do código:

```bash
ruff check src/ tests/
```

## Status do projeto e próximos passos

Esta entrega tem como elicitar requisitos para guiar o desenvolvimento do projeto.

Os próximos passos estão organizados no quadro do GitHub Projects:

**[Projeto MC656 no GitHub Projects](https://github.com/users/GiizAzul/projects/1)**

- **Issues:** as issues com a label `Atividade3` vieram do levantamento de
  requisitos da Atividade 3 (épicos e histórias de usuário com critérios de
  aceitação) e formam o backlog priorizado do projeto.
- **Documentação:** o processo de elicitação, a análise, os requisitos, os
  épicos, as histórias e a priorização estão explicados em detalhe em
  [`docs/A3_report/`](docs/A3_report).