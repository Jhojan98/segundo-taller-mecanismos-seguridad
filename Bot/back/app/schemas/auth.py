"""Esquemas Pydantic del flujo de autenticación web."""
from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    """Código de acceso generado por el bot con el comando `/web`."""

    codigo: str = Field(min_length=6, max_length=64, description="Código de un solo uso")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    usuario: UserOut
