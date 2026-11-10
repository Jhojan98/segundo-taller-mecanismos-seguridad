"""Generación y validación de tokens JWT para el acceso web.

La identidad del token es el `telegram_id` del usuario: de esta forma la sesión
web queda vinculada a la cuenta de Telegram que generó el código de acceso.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.utils.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)

if settings.jwt_secret_key:
    _SECRET_KEY = settings.jwt_secret_key
else:
    # Respaldo para desarrollo: secreto efímero por proceso. Si no se define
    # JWT_SECRET_KEY, las sesiones caducan al reiniciar el contenedor.
    logger.warning(
        "JWT_SECRET_KEY no está definido: se generó un secreto efímero solo para este proceso."
    )
    _SECRET_KEY = secrets.token_urlsafe(48)


def create_access_token(telegram_id: int) -> str:
    """Crea un token JWT firmado para el `telegram_id` indicado."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(telegram_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "typ": "access",
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """Valida el token y devuelve el `telegram_id`.

    Lanza `UnauthorizedError` si el token es inválido, ha expirado o su
    estructura no corresponde a un token de acceso.
    """
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token inválido o expirado") from exc

    subject = payload.get("sub")
    if not subject or not str(subject).isdigit():
        raise UnauthorizedError("Token inválido o expirado")
    if payload.get("typ") != "access":
        raise UnauthorizedError("Token inválido o expirado")
    return int(subject)


def generate_numeric_code(length: int = 8) -> str:
    """Genera un código aleatorio de un solo uso (letras y dígitos sin ambiguos)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))
