"""Endpoints de ubicaciones: propias, compartidas e historial autorizado."""
from fastapi import APIRouter, Query

from app.schemas import LocationOut, SharedLocationOut, UserOut
from app.services import location_service
from app.utils.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/locations", tags=["ubicaciones"])


@router.get("/me", response_model=list[LocationOut], summary="Ubicaciones propias")
def my_locations(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200, description="Cantidad máxima de registros"),
) -> list[LocationOut]:
    """Historial propio del usuario autenticado (más reciente primero)."""
    return [
        LocationOut.model_validate(location)
        for location in location_service.list_own(db, current_user.id, limit)
    ]


@router.get(
    "/shared",
    response_model=list[SharedLocationOut],
    summary="Últimas ubicaciones compartidas conmigo",
)
def shared_locations(db: DbSession, current_user: CurrentUser) -> list[SharedLocationOut]:
    """Última ubicación de cada usuario que autorizó al consultante y comparte.

    El backend valida dos condiciones por cada registro: autorización vigente y
    compartición habilitada por el propietario.
    """
    return [
        SharedLocationOut(
            usuario=UserOut.model_validate(user),
            ubicacion=LocationOut.model_validate(location),
        )
        for user, location in location_service.shared_with_me(db, current_user.id)
    ]


@router.get(
    "/history/{user_id}",
    response_model=list[LocationOut],
    summary="Historial autorizado de un usuario",
)
def location_history(
    user_id: int,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200, description="Cantidad máxima de registros"),
) -> list[LocationOut]:
    """Historial de `user_id`. Devuelve 403 si no hay autorización vigente."""
    return [
        LocationOut.model_validate(location)
        for location in location_service.history_for(db, current_user.id, user_id, limit)
    ]


@router.get(
    "/latest/{user_id}",
    response_model=LocationOut | None,
    summary="Última ubicación autorizada de un usuario",
)
def latest_location(user_id: int, db: DbSession, current_user: CurrentUser) -> LocationOut | None:
    """Última ubicación de `user_id` si el consultante está autorizado.

    Devuelve `null` cuando existe permiso pero aún no hay ubicaciones.
    """
    location = location_service.latest_for(db, current_user.id, user_id)
    return LocationOut.model_validate(location) if location else None
