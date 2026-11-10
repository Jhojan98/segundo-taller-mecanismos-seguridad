"""Modelo de configuración de privacidad del usuario."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User
from app.utils.dates import utcnow


class UserConfig(Base):
    """Preferencias de compartición de un usuario.

    `compartir_ubicacion` es el interruptor de consentimiento: cuando está en
    `False` el sistema no entrega sus ubicaciones a terceros, aunque exista una
    autorización vigente.
    """

    __tablename__ = "configuraciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    compartir_ubicacion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    # Extensión: permite enviar al usuario un aviso cuando se modifica su configuración
    notificaciones: Mapped[str] = mapped_column(String(16), default="activas", nullable=False)

    usuario: Mapped[User] = relationship()  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<UserConfig usuario={self.usuario_id} compartir={self.compartir_ubicacion}>"
