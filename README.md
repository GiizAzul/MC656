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

O repositório está dividido em duas pastas, correspondentes às duas atividades
da disciplina realizadas até o momento:

- **`A1/`** — arquivos em LaTeX e PDF que definem  o processo de
  desenvolvimento do projeto (Atividade 1).
- **`A2/`** — todo o projeto descrito neste README (Atividade 2): código-fonte,
  testes e o `main.py` da aplicação.

As seções abaixo (estrutura, como rodar, testes) se referem ao conteúdo da
pasta `A2/`.

## Estrutura do projeto

> ⚠️ **Status: prévia inicial.** Esta versão cobre a lógica central do projeto e uma interface de linha de comando (CLI) mínima para navegar por ela..

```
.
├── A1/                         # Atividade 1: documentação do processo (LaTeX/PDF)
└── A2/                         # Atividade 2: implementação do projeto
    ├── main.py                    # ponto de entrada da aplicação
    ├── requirements.txt           # dependências de teste/lint
    ├── src/
    │   ├── caco.py                # motor da Assembleia do CACo
    │   ├── australia.py           # motor da Eleição Austrália (voto transferível)
    │   ├── botc.py                # motor do Blood on the Clocktower
    │   ├── interfaces.py          # interface comum aos motores de votação
    │   ├── autenticacao/          # usuários, perfis (escopos) e serviço de login
    │   └── cli/                   # loop principal e telas do terminal
    │       ├── app.py
    │       ├── sessao.py
    │       ├── cli_utils.py
    │       └── telas/             # uma tela por fluxo (login, cadastro, cada contexto, etc.)
    └── tests/                     # testes automatizados (pytest) de domínio e de interface
```

## Requisitos

- Python 3.10 ou superior.
- Não há dependências externas para rodar a aplicação. O `requirements.txt` lista somente ferramentas de desenvolvimento (testes e lint).

## Como rodar

A partir da pasta `A2/` (raiz do código do projeto):

```bash
cd A2
python3 main.py
```

> O programa precisa ser executado a partir da raiz de `A2/`, pois os
> módulos são importados como `src...`.

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

Também a partir da pasta `A2/`:

```bash
pip install -r requirements.txt
pytest
```


Para checar o estilo do código:

```bash
ruff check .
```

## Status do projeto e próximos passos

Esta entrega tem como foco validar a lógica de negócio de cada sistema eleitoral e uma navegação básica entre as telas. Alguns dos próximos passos já mapeados para as próximas entregas da disciplina, organizados por área, são:

#### Autenticação
- Salvar usuário entre as sessões

#### Eleição da Austrália
- Validação de duas camadas para candidatos com o mesmo nome
- Impedir que o mesmo usuário vote duas vezes

#### Assembleia do CACo
- Tempo de votação
- Conferir se o votante está na lista de estudantes

#### Blood on the Clocktower
- Implementar toda a mecânica do jogo de girar "ao redor do relógio",
  conferindo jogador por jogador

#### Interface
- Permitir mais de uma votação por sessão (hoje, para uma nova votação do CACo, por exemplo, após uma votação ser encerrada é necessário iniciar uma nova sessão)
- Desenvolver uma interface propriamente dita, não em terminal

Essas melhorias, entre outras, serão trabalhadas nas próximas entregas do
projeto.