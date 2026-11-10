"""Modelo de ubicación geográfica compartida voluntariamente."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User
from app.utils.dates import utcnow


class Location(Base):
    """Registro de una ubicación enviada por el usuario mediante Telegram.

    Las coordenadas provienen exclusivamente del dispositivo del usuario
    (botón de ubicación de Telegram). La precisión se almacena como `NULL`
    cuando Telegram no la informa.
    """

    __tablename__ = "ubicaciones"
    __table_args__ = (
        CheckConstraint("latitud BETWEEN -90 AND 90", name="ck_ubicacion_latitud"),
        CheckConstraint("longitud BETWEEN -180 AND 180", name="ck_ubicacion_longitud"),
        Index("ix_ubicaciones_usuario_fecha", "usuario_id", "fecha_hora"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    latitud: Mapped[float] = mapped_column(nullable=False)
    longitud: Mapped[float] = mapped_column(nullable=False)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    usuario: Mapped[User] = relationship(back_populates="ubicaciones")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<Location id={self.id} usuario={self.usuario_id} lat={self.latitud} lon={self.longitud}>"
