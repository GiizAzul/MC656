# MC656

Repositório para o projeto da disciplina MC656 – Engenharia de Software (UNICAMP).

## Membros

|Name|RA|
|-|-|
|Giovana Jacome Marchetti|177700|
|Caio Lima Albuquerque|288808|
|Samuel Rodrigues Ferreira|195440|
|Julia de Souza Nardo|281272|
|Leonardo Carvalho De Luca|288820|

## Sobre o projeto

O projeto é um sistema de votação **web** (FastAPI + templates Jinja2) capaz de
operar em três contextos eleitorais diferentes, cada um com suas próprias regras
de apuração e perfis de usuário:

- **Assembleia do CACo** — votação de pauta por Aprovar / Rejeitar / Abster-se,
  com quórum mínimo de eleitores e um ciclo de votação com duração definida.
- **Eleição da Austrália** — voto único transferível (ranking de candidatos, com
  eliminação e transferência de votos por rodadas até haver maioria absoluta).
- **Blood on the Clocktower** — votação de execução, em que um jogador nomeado   precisa de votos maiores ou iguais à metade dos jogadores vivos para ser  executado.

## Organização do repositório

O repositório reúne o código da aplicação e a documentação das atividades da
disciplina (em `docs/`):

- **`src/` e `tests/`** — a aplicação web (motores de votação, autenticação,
  rotas e telas) e sua suíte de testes.
- **`docs/A1_report/`** — relatório da Atividade 1 (LaTeX e PDF) com a definição
  do processo de desenvolvimento, incluindo diagramas (casos de uso, domínio,
  processo) e protótipos de telas.
- **`docs/A3_report/`** — relatório da Atividade 3 (LaTeX e PDF): elicitação e
  análise de requisitos, épicos, histórias de usuário com critérios de aceitação
  e backlog priorizado.
- **`docs/A4_report/`** — relatório da Atividade 4 (LaTeX e PDF): projeto e arquitetura de software, com identificação de problemas e code smells, além da documentação da refatoração.
- **`.github/workflows/`** — pipelines de CI (`ci.yml`) e de análise estática de qualidade (`sonar.yml`). 
## Estrutura do projeto

```
.
├── requirements.txt               # dependências da aplicação, de testes e de lint
├── sonar-project.properties       # configuração do SonarQube Cloud
├── src/
│   ├── main.py                    # ponto de entrada: app FastAPI, dados de demonstração e registro das rotas
│   ├── interfaces.py              # SistemaEleitoral: interface comum aos motores (contexto do padrão State)
│   ├── estados.py                 # estados da votação: Aguardando, Em votação, Encerrada
│   ├── caco.py                    # motor da Assembleia do CACo
│   ├── australia.py               # motor da Eleição Austrália (voto transferível)
│   ├── botc.py                    # motor do Blood on the Clocktower (votos com modificadores)
│   ├── autenticacao/              # usuários, perfis (escopos), cadastro (factory) e controle de acesso
│   ├── routers/                   # rotas web: auth, caco, australia e botc
│   ├── templates/                 # telas HTML (Jinja2): login, cadastro, dashboard, admin e uma por contexto
│   └── static/                    # estilos (CSS)
├── tests/                         # testes automatizados (pytest): motores, autenticação, estados e rotas web
├── docs/
│   ├── A1_report/                 # Atividade 1: processo de desenvolvimento
│   └── A3_report/                 # Atividade 3: requisitos
│   └── A4_report/                 # Atividade 4: projeto e arquitetura de software
└── .github/workflows/             # CI: build, lint (ruff) e testes (pytest + cobertura)
```

## Requisitos

- Python 3.10 ou superior.
- Dependências listadas em `requirements.txt`: FastAPI (`fastapi[standard]`) e
  Jinja2 para a aplicação, e pytest, pytest-cov e ruff para testes e lint.

## Como rodar

A partir da raiz do repositório, crie um ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate      # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Suba o servidor:

```bash
fastapi dev src/main.py
```

Também é possível usar `uvicorn src.main:app --reload`. Depois, acesse
<http://127.0.0.1:8000>, que abre a tela de login. A documentação interativa da
API fica em <http://127.0.0.1:8000/docs>.

Os dados ficam **em memória**: ao reiniciar o servidor, usuários cadastrados e
votos são perdidos.

Na tela inicial é possível **criar uma conta nova** (escolhendo o perfil) ou
**entrar** com um dos usuários de demonstração pré-cadastrados em `src/main.py`:

| Usuário | Senha     | Perfil                          |
|---------|-----------|---------------------------------|
| `caio`  | `senha123`| Eleitor (Eleição Austrália)     |
| `julia` | `admin`   | Gestão do CACo                  |
| `leo`   | `botc123` | Jogador (BotC)                  |

Para cada contexto também já existem dados iniciais de demonstração.

## Como rodar os testes

Também a partir da raiz do repositório, com as dependências instaladas:

```bash
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

Os próximos passos estão organizados no quadro do GitHub Projects: 

**[Projeto MC656 no GitHub Projects](https://github.com/users/GiizAzul/projects/1)**