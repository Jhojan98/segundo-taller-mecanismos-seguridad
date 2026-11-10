"""Conexión a la base de datos y configuración de sesiones de SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# `pool_pre_ping=True` reactiva las conexiones caídas (útil con PostgreSQL en Docker)
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Clase base declarativa de la que derivan todos los modelos ORM."""


def get_db():
    """Dependencia de FastAPI: entrega una sesión y la libera al finalizar la petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
