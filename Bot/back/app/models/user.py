"""Modelo de usuario registrado a través del bot de Telegram."""
from datetime import datetime

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.dates import utcnow


class User(Base):
    """Usuario que inició conversación con el bot.

    El identificador principal es `telegram_id`; el número telefónico es
    opcional y solo se almacena si el usuario lo comparte voluntariamente
    mediante el botón de contacto de Telegram.
    """

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    nombre: Mapped[str | None] = mapped_column(String(128))
    telefono: Mapped[str | None] = mapped_column(String(32))
    fecha_registro: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    estado: Mapped[str] = mapped_column(String(16), default="activo", nullable=False)

    # Relaciones (solo lectura desde la API; se gestionan en los servicios)
    invitaciones_emitidas: Mapped[list["Invitation"]] = relationship(  # noqa: F821
        back_populates="emisor",
        foreign_keys="Invitation.usuario_emisor_id",
    )
    invitaciones_recibidas: Mapped[list["Invitation"]] = relationship(  # noqa: F821
        back_populates="receptor",
        foreign_keys="Invitation.usuario_receptor_id",
    )
    ubicaciones: Mapped[list["Location"]] = relationship(  # noqa: F821
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<User id={self.id} telegram_id={self.telegram_id}>"
