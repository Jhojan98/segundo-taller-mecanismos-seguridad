"""Esquemas generales: salud del sistema y configuración de privacidad."""
from datetime import datetime

from pydantic import BaseModel, field_serializer

from app.utils.dates import to_iso_utc


class HealthOut(BaseModel):
    """Respuesta de `/api/health`."""

    status: str
    database: str
    bot: str
    timestamp: str


class ConfigOut(BaseModel):
    """Estado de la compartición de ubicación del usuario."""

    model_config = {"from_attributes": True}

    compartir_ubicacion: bool
    fecha_actualizacion: datetime

    @field_serializer("fecha_actualizacion")
    def _serialize_fecha_actualizacion(self, value: datetime) -> str | None:
        return to_iso_utc(value)


class ConfigUpdate(BaseModel):
    """Cuerpo para activar o detener la compartición de ubicación."""

    compartir_ubicacion: bool
