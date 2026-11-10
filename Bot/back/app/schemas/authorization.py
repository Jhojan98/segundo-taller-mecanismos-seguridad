"""Esquemas Pydantic relacionados con autorizaciones (consentimiento)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.user import UserOut
from app.utils.dates import to_iso_utc


class AuthorizationOut(BaseModel):
    """Autorización vista desde el usuario autenticado.

    `usuario` es la contraparte; `rol` indica si el usuario autenticado es el
    propietario de la ubicación o el autorizado a consultarla.
    """

    id: int
    estado: str
    rol: Literal["propietario", "autorizado"]
    fecha_autorizacion: datetime | None = None
    fecha_revocacion: datetime | None = None
    usuario: UserOut

    @field_serializer("fecha_autorizacion")
    def _serialize_fecha_autorizacion(self, value: datetime | None) -> str | None:
        return to_iso_utc(value)

    @field_serializer("fecha_revocacion")
    def _serialize_fecha_revocacion(self, value: datetime | None) -> str | None:
        return to_iso_utc(value)


class AuthorizationCreate(BaseModel):
    """Cuerpo para crear (o reactivar) una autorización de ubicación."""

    usuario_id: int = Field(gt=0, description="Id del usuario vinculado al que se autoriza")
