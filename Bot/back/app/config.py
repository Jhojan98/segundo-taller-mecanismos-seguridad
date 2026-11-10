"""Configuración central del backend.

Todos los valores sensibles (token de Telegram, credenciales de PostgreSQL y
clave JWT) se leen desde variables de entorno o desde el archivo `.env`.
Ningún secreto vive dentro del código fuente.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de la aplicación leídos del entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram ---
    telegram_bot_token: str = ""

    # --- PostgreSQL ---
    database_url: str = (
        "postgresql+psycopg2://location_user:change_this_password@localhost:5432/location_mvp"
    )

    # --- Autenticación web (JWT) ---
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # Caducidad de los códigos de acceso web generados desde el bot (/web)
    web_code_expire_minutes: int = 5
    # Caducidad de los códigos de invitación de vinculación (/vincular)
    invitation_expire_minutes: int = 15

    # --- Servidor ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    frontend_url: str = "http://localhost:3000"

    # --- Privacidad ---
    # Política de retención: las ubicaciones más antiguas deben eliminarse.
    location_retention_days: int = 30

    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista de orígenes permitidos para CORS (separados por coma)."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Instancia única de la configuración (se cachea por proceso)."""
    return Settings()


settings = get_settings()
