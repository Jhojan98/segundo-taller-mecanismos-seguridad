"""Modelo de código de acceso web generado desde el bot."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User
from app.utils.dates import utcnow


class WebLoginCode(Base):
    """Código de un solo uso y con caducidad para iniciar sesión en la web.

    Solo puede generarlo el propio usuario desde Telegram (`/web`), por lo que
    quien conoce el código demostra control de su cuenta de Telegram.
    """

    __tablename__ = "codigos_web"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    fecha_expiracion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    utilizado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    usuario: Mapped[User] = relationship()  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<WebLoginCode id={self.id} utilizado={self.utilizado}>"
