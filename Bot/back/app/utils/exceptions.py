"""Excepciones de dominio y su traducción a respuestas HTTP.

Los servicios de negocio lanzan estas excepciones (sin conocer FastAPI) y un
manejador global las convierte en respuestas JSON con el código HTTP
correspondiente, sin exponer información interna ni trazas.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Error de negocio genérico (HTTP 400)."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """Recurso inexistente (HTTP 404)."""

    status_code = 404


class PermissionDeniedError(DomainError):
    """La identidad autenticada no tiene permiso (HTTP 403)."""

    status_code = 403


class UnauthorizedError(DomainError):
    """Autenticación ausente o inválida (HTTP 401)."""

    status_code = 401


class ConflictError(DomainError):
    """Operación en conflicto con el estado actual (HTTP 409)."""

    status_code = 409


class InvalidInputError(DomainError):
    """Datos de entrada inválidos (HTTP 422)."""

    status_code = 422


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de errores de la aplicación."""

    @app.exception_handler(DomainError)
    async def _handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Nunca se filtran detalles internos (stack trace, secretos, SQL, etc.)
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor. Consulte los registros del backend."},
        )
