"""Servicio de autenticación web basado en códigos emitidos por el bot.

Flujo:
1. El usuario abre Telegram y envía `/web` al bot.
2. El bot genera un código aleatorio de un solo uso con caducidad corta.
3. El usuario introduce ese código en la página de inicio de sesión web.
4. El backend canjea el código por un JWT firmado cuyo `sub` es su `telegram_id`.

De esta forma la sesión web queda vinculada a la cuenta de Telegram y el
frontend no puede elegir libremente qué identidad usar.
"""
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, WebLoginCode
from app.utils.dates import utcnow
from app.utils.exceptions import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    UnauthorizedError,
)
from app.utils.security import create_access_token, decode_access_token, generate_numeric_code

logger = logging.getLogger(__name__)


def create_web_code(db: Session, user_id: int) -> str:
    """Crea un código de acceso web para el usuario.

    Los códigos anteriores no utilizados se invalidan para que solo exista uno
    activo por usuario.
    """
    stmt = select(WebLoginCode).where(
        WebLoginCode.usuario_id == user_id,
        WebLoginCode.utilizado.is_(False),
    )
    for old_code in db.scalars(stmt).all():
        old_code.utilizado = True  # invalidación

    codigo = generate_numeric_code(length=8)
    while db.scalar(select(WebLoginCode).where(WebLoginCode.codigo == codigo)) is not None:
        codigo = generate_numeric_code(length=8)

    record = WebLoginCode(
        codigo=codigo,
        usuario_id=user_id,
        fecha_creacion=utcnow(),
        fecha_expiracion=utcnow() + timedelta(minutes=settings.web_code_expire_minutes),
        utilizado=False,
    )
    db.add(record)
    db.commit()
    logger.info("Código web generado para el usuario %s", user_id)
    return codigo


def exchange_web_code(db: Session, codigo: str) -> User:
    """Canjea un código de acceso web por su usuario (un solo uso)."""
    codigo_limpio = (codigo or "").strip().upper()
    if not codigo_limpio:
        raise InvalidInputError("Debes indicar el código de acceso")

    record = db.scalar(select(WebLoginCode).where(WebLoginCode.codigo == codigo_limpio))
    if record is None:
        raise UnauthorizedError("Código de acceso inválido")

    if record.utilizado:
        raise ConflictError("El código de acceso ya fue utilizado")

    if record.fecha_expiracion < utcnow():
        raise InvalidInputError("El código de acceso ha expirado. Genera uno nuevo con /web en el bot")

    user = db.get(User, record.usuario_id)
    if user is None or user.estado != "activo":
        raise UnauthorizedError("Usuario no encontrado o inactivo")

    record.utilizado = True
    db.commit()
    return user


def issue_token(db: Session, codigo: str) -> tuple[str, User]:
    """Canjea el código y devuelve `(token_jwt, usuario)`."""
    user = exchange_web_code(db, codigo)
    token = create_access_token(user.telegram_id)
    return token, user


def get_user_from_token(db: Session, token: str) -> User:
    """Resuelve el usuario a partir de un JWT (identidad = telegram_id)."""
    telegram_id = decode_access_token(token)
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None or user.estado != "activo":
        raise NotFoundError("Usuario no encontrado")
    return user
