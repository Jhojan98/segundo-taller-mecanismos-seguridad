"""Endpoint de configuración de privacidad (compartición de ubicación)."""
import logging

from fastapi import APIRouter

from app.schemas import ConfigOut, ConfigUpdate
from app.services import config_service
from app.utils.deps import CurrentUser, DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["configuración"])


@router.get("", response_model=ConfigOut, summary="Estado de la compartición")
def get_config(db: DbSession, current_user: CurrentUser) -> ConfigOut:
    """Devuelve si el usuario tiene activada la compartición de su ubicación."""
    return ConfigOut.model_validate(config_service.get(db, current_user.id))


@router.put("", response_model=ConfigOut, summary="Activar/detener la compartición")
def update_config(
    payload: ConfigUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ConfigOut:
    """Activa o detiene la compartición (equivalente web de `/detener`).

    Cuando está desactivada, el backend no entrega las ubicaciones del usuario
    a terceros aunque exista una autorización vigente.
    """
    config = config_service.set_sharing(db, current_user.id, payload.compartir_ubicacion)
    logger.info(
        "Usuario %s %s la compartición de ubicación",
        current_user.id,
        "activó" if payload.compartir_ubicacion else "detuvo",
    )
    return ConfigOut.model_validate(config)
