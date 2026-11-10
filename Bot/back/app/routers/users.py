"""Endpoints de usuarios: identidad autenticada y contactos vinculados."""
from fastapi import APIRouter

from app.schemas import ContactOut, UserOut
from app.services import authorization_service, user_service
from app.utils.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/users", tags=["usuarios"])


@router.get("/me", response_model=UserOut, summary="Usuario autenticado")
def read_me(current_user: CurrentUser) -> UserOut:
    """Devuelve la identidad derivada del token JWT (nunca de un parámetro libre)."""
    return UserOut.model_validate(current_user)


@router.get("", response_model=list[ContactOut], summary="Contactos vinculados y permisos")
def list_users(db: DbSession, current_user: CurrentUser) -> list[ContactOut]:
    """Lista los usuarios vinculados al usuario autenticado.

    Para cada contacto se indica si existe una autorización vigente en cada
    dirección. Solo se muestran usuarios con los que existe una vinculación.
    """
    contacts: list[ContactOut] = []
    for user, linked_at in user_service.list_contacts(db, current_user.id):
        ve_mi_ubicacion = (
            authorization_service.get_active(db, current_user.id, user.id) is not None
        )
        ve_su_ubicacion = (
            authorization_service.get_active(db, user.id, current_user.id) is not None
        )
        contacts.append(
            ContactOut(
                usuario=UserOut.model_validate(user),
                puede_ver_mi_ubicacion=ve_mi_ubicacion,
                puede_ver_su_ubicacion=ve_su_ubicacion,
                vinculado_desde=linked_at,
            )
        )
    return contacts
