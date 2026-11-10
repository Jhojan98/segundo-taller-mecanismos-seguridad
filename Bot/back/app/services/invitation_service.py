"""Servicio de invitaciones: generación y canje de códigos de vinculación."""
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Authorization, Invitation
from app.services import authorization_service
from app.utils.dates import utcnow
from app.utils.exceptions import ConflictError, InvalidInputError, NotFoundError
from app.utils.security import generate_numeric_code

logger = logging.getLogger(__name__)


def create(db: Session, emisor_id: int) -> Invitation:
    """Genera un código de invitación aleatorio, de un solo uso y con caducidad."""
    codigo = generate_numeric_code(length=8)
    # Se evita la (improbable) colisión con un código existente
    while db.scalar(select(Invitation).where(Invitation.codigo == codigo)) is not None:
        codigo = generate_numeric_code(length=8)

    invitation = Invitation(
        codigo=codigo,
        usuario_emisor_id=emisor_id,
        fecha_creacion=utcnow(),
        fecha_expiracion=utcnow() + timedelta(minutes=settings.invitation_expire_minutes),
        utilizado=False,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    logger.info("Invitación creada para el usuario %s", emisor_id)
    return invitation


def redeem(db: Session, codigo: str, receptor_id: int) -> tuple[Invitation, Authorization]:
    """Canjea un código de invitación y crea la autorización pendiente.

    Validaciones: existencia, caducidad, no reutilización y que el emisor y el
    receptor sean personas distintas.
    """
    codigo_limpio = (codigo or "").strip().upper()
    if not codigo_limpio:
        raise InvalidInputError("Debes indicar el código de invitación: /vincular CODIGO")

    invitation = db.scalar(select(Invitation).where(Invitation.codigo == codigo_limpio))
    if invitation is None:
        raise NotFoundError("El código de invitación no existe")

    if invitation.utilizado:
        raise ConflictError("El código de invitación ya fue utilizado")

    if invitation.fecha_expiracion < utcnow():
        raise InvalidInputError("El código de invitación ha expirado. Solicita uno nuevo con /vincular")

    if invitation.usuario_emisor_id == receptor_id:
        raise InvalidInputError("No puedes vincularte contigo mismo")

    invitation.utilizado = True
    invitation.usuario_receptor_id = receptor_id
    invitation.fecha_uso = utcnow()

    # La relación queda PENDIENTE hasta que el emisor consienta explícitamente
    authorization = authorization_service.create_pending(
        db, propietario_id=invitation.usuario_emisor_id, autorizado_id=receptor_id
    )
    db.commit()
    db.refresh(invitation)
    logger.info("Invitación %s canjeada por el usuario %s", invitation.id, receptor_id)
    return invitation, authorization


def list_emitted(db: Session, emisor_id: int) -> list[Invitation]:
    """Invitaciones emitidas por un usuario (para mostrar su estado)."""
    stmt = (
        select(Invitation)
        .where(Invitation.usuario_emisor_id == emisor_id)
        .order_by(Invitation.fecha_creacion.desc())
    )
    return list(db.scalars(stmt).all())
