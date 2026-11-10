"""Funciones de fecha y hora.

Se trabaja con UTC "naivo" (sin información de zona horaria) para que los
valores sean compatibles tanto con PostgreSQL (`timestamp without time zone`)
como con SQLite durante las pruebas. En la API se serializan siempre con
sufijo `Z` para que el navegador los interprete en UTC.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Fecha y hora actuales en UTC sin tzinfo."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_iso_utc(value: datetime | None) -> str | None:
    """Convierte un datetime a ISO-8601 en UTC terminado en `Z`."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
