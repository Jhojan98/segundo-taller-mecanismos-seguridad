"""Dependencias compartidas por los routers de la API."""
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services import user_service
from app.utils.exceptions import UnauthorizedError
from app.utils.security import decode_access_token

# `auto_error=False`: si no hay cabecera Authorization devolvemos nuestro 401
# en lugar del 403 genérico de FastAPI.
bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_user(credentials: Credentials, db: DbSession) -> User:
    """Resuelve la identidad autenticada a partir del JWT `Authorization: Bearer`.

    El `sub` del token es el `telegram_id`; por tanto, el frontend nunca decide
    qué usuario es, sino que la identidad se deriva del token firmado.
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Autenticación requerida")

    telegram_id = decode_access_token(credentials.credentials)
    user = user_service.get_by_telegram_id(db, telegram_id)
    if user is None or user.estado != "activo":
        raise UnauthorizedError("Usuario no encontrado o inactivo")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
