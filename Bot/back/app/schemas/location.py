"""Esquemas Pydantic relacionados con ubicaciones."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.user import UserOut
from app.utils.dates import to_iso_utc


class LocationOut(BaseModel):
    """Ubicación geográfica almacenada."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    latitud: float
    longitud: float
    precision: float | None = None
    fecha_hora: datetime

    @field_serializer("fecha_hora")
    def _serialize_fecha_hora(self, value: datetime) -> str | None:
        return to_iso_utc(value)


class SharedLocationOut(BaseModel):
    """Última ubicación de un usuario que autorizó su consulta."""

    usuario: UserOut
    ubicacion: LocationOut
