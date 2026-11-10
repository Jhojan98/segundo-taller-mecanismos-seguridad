"""Servicio de ubicaciones: registro y consultas con control de permisos."""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Authorization, Location, User
from app.models.authorization import ESTADO_ACTIVA
from app.services import authorization_service, config_service
from app.utils.dates import utcnow
from app.utils.exceptions import InvalidInputError, PermissionDeniedError

logger = logging.getLogger(__name__)


def _ensure_can_view(db: Session, viewer_id: int, owner_id: int) -> None:
    """Valida que el consultante pueda ver las ubicaciones del propietario.

    Reglas:
    - El propietario siempre puede consultar sus propias ubicaciones.
    - Para terceros se exige una autorización vigente (`activa`).
    - Además, el propietario debe tener activada la compartición
      (`configuracion.compartir_ubicacion = true`).
    """
    if viewer_id == owner_id:
        return

    auth = authorization_service.get_active(db, propietario_id=owner_id, autorizado_id=viewer_id)
    if auth is None:
        raise PermissionDeniedError(
            "No existe una autorización vigente para consultar las ubicaciones de este usuario"
        )

    config = config_service.get(db, owner_id)
    if not config.compartir_ubicacion:
        raise PermissionDeniedError(
            "Este usuario no tiene activada la compartición de su ubicación"
        )


def record(
    db: Session,
    user_id: int,
    latitud: float,
    longitud: float,
    precision: float | None = None,
) -> Location:
    """Almacena una ubicación enviada voluntariamente por el usuario.

    Valida el rango de coordenadas y activa la compartición, porque el envío de
    una ubicación implica un consentimiento explícito del momento.
    """
    if not -90.0 <= latitud <= 90.0:
        raise InvalidInputError("Latitud fuera de rango (-90 a 90)")
    if not -180.0 <= longitud <= 180.0:
        raise InvalidInputError("Longitud fuera de rango (-180 a 180)")

    location = Location(
        usuario_id=user_id,
        latitud=float(latitud),
        longitud=float(longitud),
        precision=float(precision) if precision is not None else None,
        fecha_hora=utcnow(),
    )
    db.add(location)
    config_service.set_sharing(db, user_id, True)
    db.commit()
    db.refresh(location)
    logger.info("Ubicación registrada para el usuario %s", user_id)
    return location


def count_for(db: Session, user_id: int) -> int:
    """Cantidad total de ubicaciones registradas de un usuario."""
    from sqlalchemy import func

    return int(
        db.scalar(select(func.count(Location.id)).where(Location.usuario_id == user_id)) or 0
    )


def latest_own(db: Session, user_id: int) -> Location | None:
    """Última ubicación del propio usuario (o `None`)."""
    return latest_for(db, viewer_id=user_id, owner_id=user_id)


def list_own(db: Session, user_id: int, limit: int = 50) -> list[Location]:
    """Historial propio del usuario, más reciente primero."""
    stmt = (
        select(Location)
        .where(Location.usuario_id == user_id)
        .order_by(Location.fecha_hora.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def latest_for(db: Session, viewer_id: int, owner_id: int) -> Location | None:
    """Última ubicación de `owner_id` si `viewer_id` está autorizado."""
    _ensure_can_view(db, viewer_id, owner_id)
    stmt = (
        select(Location)
        .where(Location.usuario_id == owner_id)
        .order_by(Location.fecha_hora.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def history_for(
    db: Session, viewer_id: int, owner_id: int, limit: int = 50
) -> list[Location]:
    """Historial autorizado de `owner_id` para `viewer_id`, más reciente primero."""
    _ensure_can_view(db, viewer_id, owner_id)
    stmt = (
        select(Location)
        .where(Location.usuario_id == owner_id)
        .order_by(Location.fecha_hora.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def shared_with_me(db: Session, viewer_id: int) -> list[tuple[User, Location]]:
    """Última ubicación de cada usuario que autorizó al consultante y comparte.

    Solo se entregan ubicaciones de usuarios con:
    1. una autorización `activa` hacia el consultante, y
    2. la compartición habilitada en su configuración.
    """
    grants = authorization_service.active_grants_to(db, viewer_id)
    owner_ids = [g.propietario_id for g in grants]
    if not owner_ids:
        return []

    sharing_ids = config_service.owners_sharing(db, owner_ids)
    if not sharing_ids:
        return []

    results: list[tuple[User, Location]] = []
    for owner_id in sharing_ids:
        latest = db.scalar(
            select(Location)
            .where(Location.usuario_id == owner_id)
            .order_by(Location.fecha_hora.desc())
            .limit(1)
        )
        if latest is None:
            continue
        owner = db.get(User, owner_id)
        if owner is not None:
            results.append((owner, latest))

    results.sort(key=lambda item: item[1].fecha_hora, reverse=True)
    return results


def purge_older_than(db: Session, days: int) -> int:
    """Elimina ubicaciones con más de `days` días (política de retención).

    Devuelve la cantidad de registros eliminados.
    """
    cutoff = utcnow() - timedelta(days=days)
    stmt = select(Location).where(Location.fecha_hora < cutoff)
    old_locations = list(db.scalars(stmt).all())
    for location in old_locations:
        db.delete(location)
    db.commit()
    if old_locations:
        logger.info("Retención: eliminadas %s ubicaciones anteriores a %s", len(old_locations), cutoff)
    return len(old_locations)


def is_recent(location: Location, days: int) -> bool:  # pragma: no cover - auxiliar
    """Indica si una ubicación es posterior a la fecha de corte."""
    return location.fecha_hora >= utcnow() - timedelta(days=days)
