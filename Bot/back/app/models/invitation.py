"""Modelo de invitación de vinculación entre usuarios."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User
from app.utils.dates import utcnow


class Invitation(Base):
    """Código de un solo uso y con caducidad para vincular dos usuarios.

    Cuando el receptor canjea el código se marca `utilizado=True`, se registra
    `usuario_receptor_id` y `fecha_uso` (extensión para auditoría), y se crea
    una `Authorization` pendiente de consentimiento explícito.
    """

    __tablename__ = "invitaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    usuario_emisor_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    fecha_expiracion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    utilizado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usuario_receptor_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    # Extensión: marca cuándo se canjeó el código (auditoría del flujo)
    fecha_uso: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    emisor: Mapped[User] = relationship(  # noqa: F821
        back_populates="invitaciones_emitidas",
        foreign_keys=[usuario_emisor_id],
    )
    receptor: Mapped[User | None] = relationship(  # noqa: F821
        back_populates="invitaciones_recibidas",
        foreign_keys=[usuario_receptor_id],
    )

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<Invitation id={self.id} codigo={self.codigo} utilizado={self.utilizado}>"
