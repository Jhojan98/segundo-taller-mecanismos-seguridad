"""Servicios de usuarios: registro, consulta y vinculaciones."""
import logging
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Invitation, User
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


def get_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    """Devuelve el usuario con ese `telegram_id` o `None` si no existe."""
    return db.scalar(select(User).where(User.telegram_id == telegram_id))


def get_by_id(db: Session, user_id: int) -> User:
    """Devuelve el usuario por su id interno o lanza `NotFoundError`."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")
    return user


def get_or_create(
    db: Session,
    *,
    telegram_id: int,
    username: str | None = None,
    nombre: str | None = None,
) -> tuple[User, bool]:
    """Registra al usuario la primera vez; después solo lo reconoce.

    Devuelve `(usuario, creado)`. No duplica registros: `telegram_id` es único.
    """
    user = get_by_telegram_id(db, telegram_id)
    if user is not None:
        # Se actualizan datos visibles si cambiaron en Telegram (sin tocar teléfono)
        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        if nombre and user.nombre != nombre:
            user.nombre = nombre
            changed = True
        if changed:
            db.commit()
        return user, False

    user = User(telegram_id=telegram_id, username=username, nombre=nombre, estado="activo")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Condición de carrera: otro proceso registró el mismo telegram_id
        db.rollback()
        existing = get_by_telegram_id(db, telegram_id)
        if existing is None:  # pragma: no cover - caso improbable
            raise
        return existing, False
    db.refresh(user)
    return user, True


def set_telefono(db: Session, user: User, telefono: str | None) -> User:
    """Almacena el teléfono solo si el usuario lo compartió voluntariamente."""
    user.telefono = telefono
    db.commit()
    return user


def list_contacts(db: Session, user_id: int) -> list[tuple[User, datetime | None]]:
    """Devuelve los usuarios vinculados mediante una invitación canjeada.

    Cada elemento es `(usuario_vinculado, fecha_de_vinculación)`.
    """
    stmt = (
        select(Invitation)
        .where(
            Invitation.utilizado.is_(True),
            or_(
                Invitation.usuario_emisor_id == user_id,
                Invitation.usuario_receptor_id == user_id,
            ),
        )
        .order_by(Invitation.fecha_uso.desc())  # type: ignore[attr-defined]
    )
    invitations = list(db.scalars(stmt).all())

    contacts: list[tuple[User, datetime | None]] = []
    seen: set[int] = set()
    for invitation in invitations:
        other_id = (
            invitation.usuario_receptor_id
            if invitation.usuario_emisor_id == user_id
            else invitation.usuario_emisor_id
        )
        if other_id is None or other_id == user_id or other_id in seen:
            continue
        seen.add(other_id)
        other = db.get(User, other_id)
        if other is not None:
            contacts.append((other, invitation.fecha_uso))
    return contacts


def are_linked(db: Session, user_id: int, other_id: int) -> bool:
    """Indica si dos usuarios tienen una vinculación canjeada (en cualquier dirección)."""
    from sqlalchemy import and_

    stmt = select(Invitation).where(
        Invitation.utilizado.is_(True),
        or_(
            and_(
                Invitation.usuario_emisor_id == user_id,
                Invitation.usuario_receptor_id == other_id,
            ),
            and_(
                Invitation.usuario_emisor_id == other_id,
                Invitation.usuario_receptor_id == user_id,
            ),
        ),
    )
    return db.scalar(stmt) is not None
