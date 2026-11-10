"""Esquemas Pydantic relacionados con invitaciones de vinculación."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.user import UserOut
from app.utils.dates import to_iso_utc


class InvitationOut(BaseModel):
    """Invitación de vinculación (código de un solo uso)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    fecha_creacion: datetime
    fecha_expiracion: datetime
    utilizado: bool
    emisor: UserOut | None = None
    receptor: UserOut | None = None

    @field_serializer("fecha_creacion")
    def _serialize_fecha_creacion(self, value: datetime) -> str | None:
        return to_iso_utc(value)

    @field_serializer("fecha_expiracion")
    def _serialize_fecha_expiracion(self, value: datetime) -> str | None:
        return to_iso_utc(value)
