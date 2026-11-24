import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src import database
from src.autenticacao.australia import EleitorAustralia
from src.autenticacao.botc import JogadorBOTC
from src.autenticacao.caco import GestaoCACo
from src.main import app


@pytest.fixture(autouse=True)
def isolar_banco_sql(monkeypatch):
    """Garante que cada teste rode com um banco SQLite em memória limpo,
    sem criar votacao.db no disco e sem vazar estado entre testes.
    """
    engine_teste = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)

    monkeypatch.setattr(database, "DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setattr(database, "engine", engine_teste)
    monkeypatch.setattr(database, "SessionLocal", SessionTeste)

    database.Base.metadata.create_all(bind=engine_teste)
    yield
    database.Base.metadata.drop_all(bind=engine_teste)
    engine_teste.dispose()

@pytest.fixture(autouse=True)
def garantir_usuarios_padrao_mock():
    """Garante que caio, julia e leo existam com seus escopos originais antes de cada teste."""
    banco = app.state.banco_auth

    usuarios_padrao = [
        EleitorAustralia("caio", "senha123", "Caio Lima"),
        GestaoCACo("julia", "admin", "Julia Nardo"),
        JogadorBOTC("leo", "botc123", "Leonardo Carvalho"),
    ]
    
    for usuario_padrao in usuarios_padrao:
        user_id = banco._mapa_usernames.get(usuario_padrao.username)
        usuario_atual = banco._banco_por_id.get(user_id) if user_id else None

        # Se não existir ou teve o escopo alterado/mesclado por algum teste anterior, recria limpo
        if not usuario_atual or usuario_atual.escopo != usuario_padrao.escopo:
            if user_id:
                banco._banco_por_id.pop(user_id, None)
            banco._mapa_usernames.pop(usuario_padrao.username, None)
            banco.registrar(usuario_padrao)