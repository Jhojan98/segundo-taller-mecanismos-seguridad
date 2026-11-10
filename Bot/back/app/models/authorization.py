"""Modelo de autorización (consentimiento) para consultar ubicaciones."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User

# Estados posibles de una autorización
ESTADO_PENDIENTE = "pendiente"
ESTADO_ACTIVA = "activa"
ESTADO_REVOCADA = "revocada"
ESTADO_RECHAZADA = "rechazada"


class Authorization(Base):
    """Consentimiento explícito del propietario para que otro usuario vea sus ubicaciones.

    - `propietario_id`: dueño de la ubicación (quien consiente).
    - `autorizado_id`: usuario que podrá consultar las ubicaciones del propietario.
    - `estado`: pendiente → activa | rechazada, y activa → revocada.
    """

    __tablename__ = "autorizaciones"
    __table_args__ = (
        UniqueConstraint("propietario_id", "autorizado_id", name="uq_autorizacion_propietario_autorizado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    propietario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    autorizado_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_autorizacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estado: Mapped[str] = mapped_column(String(16), default=ESTADO_PENDIENTE, nullable=False)
    fecha_revocacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relaciones unidireccionales hacia los usuarios implicados
    propietario: Mapped[User] = relationship(foreign_keys=[propietario_id])  # noqa: F821
    autorizado: Mapped[User] = relationship(foreign_keys=[autorizado_id])  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return (
            f"<Authorization id={self.id} propietario={self.propietario_id} "
            f"autorizado={self.autorizado_id} estado={self.estado}>"
        )
