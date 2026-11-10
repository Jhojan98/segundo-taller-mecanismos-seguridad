"""Endpoints de invitaciones: generación y estado de los códigos de vinculación."""
import logging

from fastapi import APIRouter

from app.schemas import InvitationOut
from app.services import invitation_service
from app.utils.deps import CurrentUser, DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invitations", tags=["invitaciones"])


@router.post("", response_model=InvitationOut, status_code=201, summary="Generar invitación")
def create_invitation(db: DbSession, current_user: CurrentUser) -> InvitationOut:
    """Genera un código aleatorio, de un solo uso y con caducidad.

    El código se entrega al usuario para que lo canjee otra persona mediante
    `/vincular CODIGO` en el bot.
    """
    invitation = invitation_service.create(db, current_user.id)
    logger.info("Invitación generada por el usuario %s", current_user.id)
    return InvitationOut.model_validate(invitation)


@router.get("", response_model=list[InvitationOut], summary="Invitaciones emitidas")
def list_invitations(db: DbSession, current_user: CurrentUser) -> list[InvitationOut]:
    """Lista las invitaciones emitidas por el usuario autenticado."""
    return [
        InvitationOut.model_validate(invitation)
        for invitation in invitation_service.list_emitted(db, current_user.id)
    ]
