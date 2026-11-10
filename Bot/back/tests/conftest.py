"""Configuración global de las pruebas.

Puntos clave:
- La base de datos de pruebas es **independiente** de la del entorno de
  ejecución: se usa `TEST_DATABASE_URL` si existe; en caso contrario un
  archivo SQLite local (`tests/test_ubicaciones.db`).
- El token de Telegram se vacía para que el ciclo de vida de FastAPI **no**
  arranque el bot durante las pruebas.
- Las tablas se recrean antes de cada prueba para aislar los datos.
"""
import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
TEST_DB_FILE = BASE_DIR / "test_ubicaciones.db"


def _ensure_postgres_database(url: str) -> None:
    """Crea la base de datos de pruebas si no existe (solo PostgreSQL)."""
    if not url.startswith(("postgres://", "postgresql://", "postgresql+psycopg2://")):
        return
    try:
        from sqlalchemy.engine import make_url

        parsed = make_url(url)
        import psycopg2

        connect_kwargs = {
            "dbname": parsed.database,
            "user": parsed.username,
            "password": parsed.password,
            "host": parsed.host or "localhost",
            "port": parsed.port or 5432,
        }
        try:
            connection = psycopg2.connect(**connect_kwargs)
            connection.close()
            return  # la base ya existe
        except psycopg2.OperationalError:
            pass

        connect_kwargs["dbname"] = "postgres"
        connection = psycopg2.connect(**connect_kwargs)
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{parsed.database}"')
        connection.close()
    except Exception as exc:  # noqa: BLE001 - si falla, pytest lo reportará después
        print(f"[conftest] No se pudo verificar/crear la base de pruebas: {exc}")


def _prepare_environment() -> None:
    """Configura las variables de entorno antes de importar la aplicación."""
    test_url = os.environ.get("TEST_DATABASE_URL", "").strip()

    if test_url:
        _ensure_postgres_database(test_url)
    else:
        # Base de datos SQLite local, eliminada al inicio de cada sesión
        if TEST_DB_FILE.exists():
            TEST_DB_FILE.unlink()
        test_url = f"sqlite:///{TEST_DB_FILE}"

    # Sobrescribe la URL principal: las pruebas jamás tocan la BD del entorno
    os.environ["DATABASE_URL"] = test_url
    os.environ.setdefault("JWT_SECRET_KEY", "clave-secreta-de-pruebas-segura-0123456789abcd")
    os.environ["TELEGRAM_BOT_TOKEN"] = ""  # el bot no arranca durante las pruebas
    os.environ.setdefault("CORS_ORIGINS", "http://testserver,http://localhost:3000")


_prepare_environment()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.utils.security import create_access_token  # noqa: E402

# Se crea el esquema de pruebas una vez por sesión
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def isolated_database():
    """Recrea las tablas antes de cada prueba para garantizar el aislamiento."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db():
    """Sesión de base de datos para pruebas de servicios."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client():
    """Cliente HTTP de prueba (ejecuta el ciclo de vida de FastAPI)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers():
    """Genera las cabeceras de autenticación para un `telegram_id` dado."""

    def _headers(telegram_id: int) -> dict[str, str]:
        token = create_access_token(telegram_id)
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.fixture()
def make_user(db):
    """Crea un usuario de prueba a partir de su `telegram_id`."""

    def _make(telegram_id: int, username: str | None = None, nombre: str | None = None):
        from app.services import user_service

        user, _created = user_service.get_or_create(
            db, telegram_id=telegram_id, username=username, nombre=nombre
        )
        return user

    return _make
