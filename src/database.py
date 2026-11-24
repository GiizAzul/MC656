import os
import pickle

from sqlalchemy import (
    Column,
    DateTime,
    LargeBinary,
    String,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./votacao.db")

# Compatibilidade com URLs postgres:// antigas usadas por algumas plataformas
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class EstadoSistema(Base):
    """Tabela SQL para persistir os estados dos módulos entre reinicializações."""

    __tablename__ = "estado_sistema"

    chave = Column(String(120), primary_key=True, index=True)
    payload = Column(LargeBinary, nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def inicializar_banco() -> None:
    """Cria as tabelas no banco SQL caso ainda não existam."""
    Base.metadata.create_all(bind=engine)

def salvar_estado_sql(itens: dict[str, object]) -> None:
    """Executa query de upsert (INSERT ou UPDATE) no banco de dados, persistindo múltiplas chaves em uma única transação SQL."""
    inicializar_banco()
    with SessionLocal() as db:
        for chave, valor in itens.items():
            dados_binarios = pickle.dumps(valor)
            registro = db.execute(
                select(EstadoSistema).where(EstadoSistema.chave == chave)
            ).scalar_one_or_none()
            if registro is None:
                db.add(EstadoSistema(chave=chave, payload=dados_binarios))
            else:
                registro.payload = dados_binarios
        db.commit()


def carregar_estado_sql(chave: str, padrao: object = None) -> object:
    """Executa query SELECT no banco de dados e retorna o estado salvo ou o padrão."""
    inicializar_banco()
    with SessionLocal() as db:
        registro = db.execute(select(EstadoSistema).where(EstadoSistema.chave == chave)).scalar_one_or_none()
        if registro is None:
            return padrao
        return pickle.loads(registro.payload)
