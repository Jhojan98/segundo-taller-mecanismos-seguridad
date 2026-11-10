"""Endpoints de autorizaciones: consulta, creación y revocación de consentimiento."""
import logging

from fastapi import APIRouter

from app.schemas import AuthorizationCreate, AuthorizationOut, UserOut
from app.services import authorization_service, user_service
from app.utils.deps import CurrentUser, DbSession
from app.utils.exceptions import InvalidInputError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/authorizations", tags=["autorizaciones"])


def _to_out(auth, role: str, other) -> AuthorizationOut:
    return AuthorizationOut(
        id=auth.id,
        estado=auth.estado,
        rol=role,  # type: ignore[arg-type]
        fecha_autorizacion=auth.fecha_autorizacion,
        fecha_revocacion=auth.fecha_revocacion,
        usuario=UserOut.model_validate(other),
    )


@router.get("", response_model=list[AuthorizationOut], summary="Autorizaciones del usuario")
def list_authorizations(db: DbSession, current_user: CurrentUser) -> list[AuthorizationOut]:
    """Autorizaciones donde el usuario es propietario o autorizado."""
    rows = authorization_service.list_for(db, current_user.id)
    return [_to_out(auth, role, other) for auth, role, other in rows]


@router.post(
    "",
    response_model=AuthorizationOut,
    status_code=201,
    summary="Crear (o reactivar) una autorización",
)
def create_authorization(
    payload: AuthorizationCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> AuthorizationOut:
    """El usuario autenticado otorga su consentimiento para compartir su ubicación.

    El propietario de los datos es quien autoriza: por eso la identidad se
    toma del token y `payload.usuario_id` solo identifica al destinatario.
    """
    target = user_service.get_by_id(db, payload.usuario_id)
    if target.id == current_user.id:
        raise InvalidInputError("No puedes autorizarte a ti mismo")
    if target.estado != "activo":
        raise InvalidInputError("El usuario destino no está activo")
    if not user_service.are_linked(db, current_user.id, target.id):
        raise InvalidInputError(
            "Primero debes vincularte con este usuario (genera un código con /vincular en el bot)"
        )

    auth = authorization_service.grant(db, propietario_id=current_user.id, autorizado_id=target.id)
    logger.info("Usuario %s autorizó a ver su ubicación a %s", current_user.id, target.id)
    return _to_out(auth, "propietario", target)


@router.delete("/{auth_id}", response_model=AuthorizationOut, summary="Revocar una autorización")
def revoke_authorization(
    auth_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> AuthorizationOut:
    """Revoca el consentimiento: a partir de ese momento deja de compartir ubicaciones."""
    auth = authorization_service.revoke(db, auth_id, current_user.id)
    other_id = auth.autorizado_id if auth.propietario_id == current_user.id else auth.propietario_id
    other = user_service.get_by_id(db, other_id)
    role = "propietario" if auth.propietario_id == current_user.id else "autorizado"
    logger.info("Autorización %s revocada", auth_id)
    return _to_out(auth, role, other)
