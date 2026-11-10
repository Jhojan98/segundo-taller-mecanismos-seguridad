"""Esquemas Pydantic relacionados con usuarios."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.utils.dates import to_iso_utc


class UserOut(BaseModel):
    """Representación pública de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None = None
    nombre: str | None = None
    telefono: str | None = None
    fecha_registro: datetime
    estado: str

    @field_serializer("fecha_registro")
    def _serialize_fecha_registro(self, value: datetime) -> str | None:
        return to_iso_utc(value)


class ContactOut(BaseModel):
    """Usuario vinculado al usuario autenticado, con el estado de permisos mutuos."""

    usuario: UserOut
    # ¿El contacto puede ver mi ubicación? (yo soy el propietario)
    puede_ver_mi_ubicacion: bool = False
    # ¿Yo puedo ver la ubicación del contacto? (él es el propietario)
    puede_ver_su_ubicacion: bool = False
    vinculado_desde: datetime | None = None

    @field_serializer("vinculado_desde")
    def _serialize_vinculado_desde(self, value: datetime | None) -> str | None:
        return to_iso_utc(value)
