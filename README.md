# MC656 — Sistema de Votação Multi-Escopo

Projeto desenvolvido para a disciplina MC656 — Engenharia de Software, na UNICAMP. A aplicação oferece uma interface web para três contextos de votação, com autenticação por perfil, regras próprias de apuração e persistência do estado em banco SQL.

## Integrantes

| Nome | RA |
|---|---:|
| Giovana Jacome Marchetti | 177700 |
| Caio Lima Albuquerque | 288808 |
| Samuel Rodrigues Ferreira | 195440 |
| Julia de Souza Nardo | 281272 |
| Leonardo Carvalho De Luca | 288820 |

## Escopos

- **Assembleia do CACo:** votação de pauta com opções aprovar, rejeitar e abster-se, controle de quórum fila de fala.
- **Eleição da Austrália:** voto único transferível, com ranking de candidatos e apuração por rodadas, eliminação e transferência de votos.
- **Blood on the Clocktower (BotC):** votação de execução de jogador, com modificadores de voto e limiar calculado a partir dos jogadores vivos.

## Tecnologias

- **Backend:** Python, FastAPI, SQLAlchemy e SQL.
- **Frontend:** React 18, React Router e Vite.
- **Qualidade:** pytest, pytest-cov, Ruff e SonarQube Cloud.

## Como acessar e executar

### Site publicado

A aplicação está disponível em <https://sistema-de-votacao-dypb.onrender.com/>. Na primeira visita, o site pode levar um pouco para abrir enquanto o serviço hospedado é iniciado.

### Executar na máquina local

Pré-requisitos: Python 3.10 ou superior, `uv`, Node.js e npm. Na raiz do repositório, crie e ative o ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Inicie o backend no primeiro terminal:

```bash
uv run uvicorn src.main:app --reload --port 8000
```

No segundo terminal, inicie o frontend:

```bash
cd frontend
npm install
npm run dev
```

Abra o endereço indicado pelo Vite, normalmente <http://localhost:5173>. O Vite encaminha as chamadas do frontend para o backend local na porta 8000. A documentação interativa da API fica em <http://127.0.0.1:8000/docs>.

## Acessos de demonstração

O sistema inicializa contas de demonstração quando o banco ainda não possui estado salvo:

| Usuário | Senha | Perfil |
|---|---|---|
| `caio` | `senha123` | Eleitor da Eleição da Austrália |
| `julia` | `admin` | Gestão do CACo |
| `leo` | `botc123` | Jogador do BotC |

Também são criados dados iniciais de demonstração para os contextos eleitorais. Cadastros e estado de votação são persistidos no banco configurado; no SQLite padrão, os dados ficam no arquivo `votacao.db` na raiz. Para começar com estado limpo, remova esse arquivo antes de iniciar a aplicação.

## Testes e estilo

Na raiz do repositório, com o ambiente virtual ativado:

```bash
pytest
```

Para gerar um resumo local da cobertura e verificar o estilo:

```bash
pytest --cov=src --cov-report=term
ruff check src/ tests/
```

O workflow de CI em `.github/workflows/ci.yml` automatiza verificações do projeto. A análise estática de qualidade está configurada em `.github/workflows/sonar.yml` e `sonar-project.properties`.

## Estrutura do repositório

```text
.
├── src/
│   ├── main.py                  # aplicação FastAPI, inicialização e integração do frontend
│   ├── database.py              # conexão SQL e persistência do estado
│   ├── caco.py                  # regras da Assembleia do CACo
│   ├── australia.py             # regras da eleição australiana
│   ├── botc.py                  # regras de votação do BotC
│   ├── autenticacao/            # usuários, perfis e autorização
│   ├── routers/                 # endpoints de autenticação e votação
│   ├── templates/               # páginas auxiliares servidas pelo backend
│   └── static/                  # recursos estáticos do backend
├── frontend/
│   ├── src/pages/               # páginas React por área do sistema
│   └── src/styles/              # estilos da interface
├── tests/                       # testes automatizados do backend
├── docs/                        # relatórios e artefatos das atividades
└── .github/workflows/           # CI e análise estática
```

## Documentação da disciplina

- [Atividade 1 — Processo de desenvolvimento (PDF)](docs/A1_report/A1_Definição_do_Processo_de_Desenvolvimento.pdf)
- [Atividade 3 — Requisitos (PDF)](docs/A3_report/Atividade_3___Requisitos.pdf)
- [Atividade 4 — Projeto e arquitetura (PDF)](docs/A4_report/Atividade_4___Projeto_e_Arquitetura_de_Software.pdf)
- [Atividade 5 — Testes de software (PDF)](docs/A5_report/Atividade_5___Teste_de_Software.pdf)

Os relatórios documentam o desenvolvimento do projeto ao longo da disciplina, incluindo processo de trabalho, requisitos, arquitetura e testes. Em conjunto, registram as decisões e práticas adotadas pela equipe na construção e avaliação do sistema.

## Quadro do projeto

O quadro reúne o planejamento e o acompanhamento do trabalho da equipe, com tarefas e atividades relacionadas ao desenvolvimento do sistema.

[Projeto MC656 no GitHub Projects](https://github.com/users/GiizAzul/projects/1)
