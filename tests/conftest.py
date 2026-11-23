import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src import database


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