"""Prueba de conexión real con PostgreSQL.

Se ejecuta solo cuando `TEST_DATABASE_URL` apunta a PostgreSQL (por ejemplo,
dentro del contenedor del backend con `docker compose exec backend pytest`).
En caso contrario la prueba queda marcada como omitida, no como superada.
"""
import os

import pytest
from sqlalchemy import text

from app.database import engine

_POSTGRES_PREFIXES = ("postgres://", "postgresql://", "postgresql+psycopg2://")
_requires_postgres = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL", "").startswith(_POSTGRES_PREFIXES),
    reason="Requiere TEST_DATABASE_URL configurada con PostgreSQL",
)


@_requires_postgres
def test_postgres_connection():
    """Verifica que el motor de SQLAlchemy conecta a PostgreSQL."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1


@_requires_postgres
def test_postgres_schema_created():
    """Comprueba que las tablas del esquema existen en PostgreSQL."""
    with engine.connect() as connection:
        for table in ("usuarios", "invitaciones", "autorizaciones", "ubicaciones", "configuraciones"):
            row = connection.execute(
                text("SELECT to_regclass(:name)"), {"name": table}
            ).scalar()
            assert row is not None, f"La tabla {table} no fue creada"
