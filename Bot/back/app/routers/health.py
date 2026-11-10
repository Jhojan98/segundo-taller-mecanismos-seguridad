"""Endpoint de comprobación de salud del sistema."""
import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.bot import state as bot_state
from app.schemas import HealthOut
from app.utils.dates import to_iso_utc, utcnow
from app.utils.deps import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["salud"])


@router.get("", response_model=HealthOut, summary="Estado del backend, la BD y el bot")
def health_check(db: DbSession) -> HealthOut:
    """Comprueba que el proceso responde y que PostgreSQL es alcanzable."""
    database_status = "ok"
    status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - se registra el error sin filtrar detalles al cliente
        logger.exception("Fallo de conexión con la base de datos")
        database_status = "error"
        status = "error"

    return HealthOut(
        status=status,
        database=database_status,
        bot=bot_state.get_status(),
        timestamp=to_iso_utc(utcnow()),
    )
