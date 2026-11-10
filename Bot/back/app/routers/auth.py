"""Endpoints de autenticación web (canje del código emitido por el bot)."""
from fastapi import APIRouter

from app.config import settings
from app.schemas import LoginRequest, LoginResponse, UserOut
from app.services import auth_service
from app.utils.deps import DbSession

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


@router.post(
    "/token",
    response_model=LoginResponse,
    summary="Intercambia el código de acceso web por un JWT",
)
def login(payload: LoginRequest, db: DbSession) -> LoginResponse:
    """Canjea el código de un solo uso generado con `/web` en el bot.

    El token emitido contiene como identidad el `telegram_id` del usuario; el
    frontend no puede elegir libremente qué identidad usar.
    """
    token, user = auth_service.issue_token(db, payload.codigo)
    return LoginResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
        usuario=UserOut.model_validate(user),
    )
