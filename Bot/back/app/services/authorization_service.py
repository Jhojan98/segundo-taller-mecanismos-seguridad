"""Servicio de autorizaciones: consentimiento para consultar ubicaciones."""
import logging
from typing import Literal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Authorization, User
from app.models.authorization import (
    ESTADO_ACTIVA,
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADA,
    ESTADO_REVOCADA,
)
from app.services import user_service
from app.utils.dates import utcnow
from app.utils.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)


def get_by_id(db: Session, auth_id: int) -> Authorization | None:
    """Devuelve una autorización por su id."""
    return db.get(Authorization, auth_id)


def get_active(db: Session, propietario_id: int, autorizado_id: int) -> Authorization | None:
    """Devuelve la autorización activa del propietario hacia el autorizado."""
    stmt = select(Authorization).where(
        Authorization.propietario_id == propietario_id,
        Authorization.autorizado_id == autorizado_id,
        Authorization.estado == ESTADO_ACTIVA,
    )
    return db.scalar(stmt)


def can_view(db: Session, viewer_id: int, owner_id: int) -> bool:
    """¿Puede `viewer_id` consultar las ubicaciones de `owner_id`?

    Siempre es verdadero para la propia ubicación; para las de terceros se
    exige una autorización vigente (`estado = activa`).
    """
    if viewer_id == owner_id:
        return True
    return get_active(db, owner_id, viewer_id) is not None


def _upsert(
    db: Session,
    propietario_id: int,
    autorizado_id: int,
    estado: str,
) -> Authorization:
    """Crea o actualiza la relación única (propietario, autorizado)."""
    stmt = select(Authorization).where(
        Authorization.propietario_id == propietario_id,
        Authorization.autorizado_id == autorizado_id,
    )
    auth = db.scalar(stmt)

    if auth is None:
        auth = Authorization(
            propietario_id=propietario_id,
            autorizado_id=autorizado_id,
            estado=estado,
            fecha_autorizacion=utcnow() if estado == ESTADO_ACTIVA else None,
        )
        db.add(auth)
    else:
        auth.estado = estado
        if estado == ESTADO_ACTIVA:
            auth.fecha_autorizacion = utcnow()
            auth.fecha_revocacion = None
        elif estado == ESTADO_REVOCADA:
            auth.fecha_revocacion = utcnow()
    db.commit()
    db.refresh(auth)
    return auth


def create_pending(db: Session, propietario_id: int, autorizado_id: int) -> Authorization:
    """Crea (o reabre) una autorización pendiente de consentimiento.

    Si ya existe una autorización activa se conserva tal cual: vincular de nuevo
    nunca debe revocar un consentimiento ya otorgado.
    """
    existing = db.scalar(
        select(Authorization).where(
            Authorization.propietario_id == propietario_id,
            Authorization.autorizado_id == autorizado_id,
        )
    )
    if existing is not None and existing.estado == ESTADO_ACTIVA:
        return existing
    return _upsert(db, propietario_id, autorizado_id, ESTADO_PENDIENTE)


def grant(db: Session, propietario_id: int, autorizado_id: int) -> Authorization:
    """Activa (o reactiva) una autorización: consentimiento explícito del propietario."""
    return _upsert(db, propietario_id, autorizado_id, ESTADO_ACTIVA)


def _get_owned(db: Session, auth_id: int, user_id: int) -> Authorization:
    """Obtiene una autorización que debe ser gestionada por `user_id` (propietario)."""
    auth = get_by_id(db, auth_id)
    if auth is None:
        raise NotFoundError("Autorización no encontrada")
    if auth.propietario_id != user_id:
        raise PermissionDeniedError("Solo el propietario de la ubicación puede gestionar esta autorización")
    return auth


def approve(db: Session, auth_id: int, user_id: int) -> Authorization:
    """El propietario aprueba una autorización pendiente."""
    auth = _get_owned(db, auth_id, user_id)
    if auth.estado == ESTADO_ACTIVA:
        return auth
    if auth.estado not in (ESTADO_PENDIENTE, ESTADO_RECHAZADA, ESTADO_REVOCADA):
        raise ConflictError("La autorización no está en un estado que permita aprobación")
    return grant(db, auth.propietario_id, auth.autorizado_id)


def reject(db: Session, auth_id: int, user_id: int) -> Authorization:
    """El propietario rechaza una autorización pendiente."""
    auth = _get_owned(db, auth_id, user_id)
    if auth.estado == ESTADO_PENDIENTE:
        auth.estado = ESTADO_RECHAZADA
        auth.fecha_revocacion = utcnow()
        db.commit()
        db.refresh(auth)
    return auth


def revoke(db: Session, auth_id: int, user_id: int) -> Authorization:
    """El propietario revoca una autorización: deja de compartir sus ubicaciones."""
    auth = _get_owned(db, auth_id, user_id)
    if auth.estado == ESTADO_REVOCADA:
        return auth
    auth.estado = ESTADO_REVOCADA
    auth.fecha_revocacion = utcnow()
    db.commit()
    db.refresh(auth)
    logger.info("Autorización %s revocada por el usuario %s", auth_id, user_id)
    return auth


def list_for(db: Session, user_id: int) -> list[tuple[Authorization, Literal["propietario", "autorizado"], User]]:
    """Devuelve todas las autorizaciones donde el usuario participa.

    Cada elemento es `(autorización, rol_del_usuario, contraparte)`.
    """
    stmt = select(Authorization).where(
        or_(
            Authorization.propietario_id == user_id,
            Authorization.autorizado_id == user_id,
        )
    ).order_by(Authorization.id.desc())
    rows: list[tuple[Authorization, Literal["propietario", "autorizado"], User]] = []
    for auth in db.scalars(stmt).all():
        if auth.propietario_id == user_id:
            role: Literal["propietario", "autorizado"] = "propietario"
            other_id = auth.autorizado_id
        else:
            role = "autorizado"
            other_id = auth.propietario_id
        other = user_service.get_by_id(db, other_id)
        rows.append((auth, role, other))
    return rows


def active_grants_to(db: Session, viewer_id: int) -> list[Authorization]:
    """Autorizaciones activas que reciben los usuarios hacia `viewer_id`."""
    stmt = select(Authorization).where(
        Authorization.autorizado_id == viewer_id,
        Authorization.estado == ESTADO_ACTIVA,
    )
    return list(db.scalars(stmt).all())
