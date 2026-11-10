"""Pruebas de invitaciones: generación, canje, caducidad y reutilización."""
from datetime import timedelta

import pytest

from app.services import authorization_service, invitation_service, user_service
from app.utils.dates import utcnow
from app.utils.exceptions import ConflictError, InvalidInputError, NotFoundError


def test_create_invitation(db, make_user):
    """La invitación se crea con código aleatorio y caducidad."""
    owner = make_user(1, username="dueno")

    invitation = invitation_service.create(db, owner.id)

    assert invitation.codigo
    assert len(invitation.codigo) == 8
    assert invitation.utilizado is False
    assert invitation.usuario_receptor_id is None
    assert invitation.fecha_expiracion > invitation.fecha_creacion


def test_invitation_codes_are_unique(db, make_user):
    """Los códigos generados no se repiten."""
    owner = make_user(1)
    codes = {invitation_service.create(db, owner.id).codigo for _ in range(20)}
    assert len(codes) == 20


def test_redeem_invitation_creates_pending_authorization(db, make_user):
    """El canje vincula a ambos usuarios con una autorización pendiente."""
    owner = make_user(1, username="dueno", nombre="Dueño")
    guest = make_user(2, username="invitado", nombre="Invitado")
    invitation = invitation_service.create(db, owner.id)

    redeemed, authorization = invitation_service.redeem(db, invitation.codigo, guest.id)

    assert redeemed.utilizado is True
    assert redeemed.usuario_receptor_id == guest.id
    assert redeemed.fecha_uso is not None
    assert authorization.estado == "pendiente"
    assert authorization.propietario_id == owner.id
    assert authorization.autorizado_id == guest.id
    # Aún no hay consentimiento: no puede consultar la ubicación
    assert authorization_service.can_view(db, guest.id, owner.id) is False


def test_invitation_single_use(db, make_user):
    """Un código no puede canjearse dos veces."""
    owner = make_user(1)
    guest_a = make_user(2)
    guest_b = make_user(3)
    invitation = invitation_service.create(db, owner.id)

    invitation_service.redeem(db, invitation.codigo, guest_a.id)

    with pytest.raises(ConflictError):
        invitation_service.redeem(db, invitation.codigo, guest_b.id)


def test_invitation_expiry(db, make_user):
    """Un código caducado no puede canjearse."""
    owner = make_user(1)
    guest = make_user(2)
    invitation = invitation_service.create(db, owner.id)
    invitation.fecha_expiracion = utcnow() - timedelta(minutes=1)
    db.commit()

    with pytest.raises(InvalidInputError):
        invitation_service.redeem(db, invitation.codigo, guest.id)


def test_invitation_not_found(db, make_user):
    """Un código inexistente se rechaza."""
    owner = make_user(1)
    with pytest.raises(NotFoundError):
        invitation_service.redeem(db, "ZZZZZZZZ", owner.id)


def test_invitation_self_link_rejected(db, make_user):
    """Nadie puede vincularse consigo mismo."""
    owner = make_user(1)
    invitation = invitation_service.create(db, owner.id)

    with pytest.raises(InvalidInputError):
        invitation_service.redeem(db, invitation.codigo, owner.id)


def test_api_create_invitation(client, auth_headers, make_user):
    """`POST /api/invitations` devuelve un código para el usuario autenticado."""
    make_user(111, username="ana")
    response = client.post("/api/invitations", headers=auth_headers(111))

    assert response.status_code == 201
    payload = response.json()
    assert payload["codigo"]
    assert payload["utilizado"] is False
    assert payload["emisor"]["telegram_id"] == 111


def test_api_invitation_requires_authentication(client):
    """Generar invitaciones exige estar autenticado."""
    response = client.post("/api/invitations")
    assert response.status_code == 401


def test_api_list_invitations(client, auth_headers, make_user):
    """`GET /api/invitations` lista solo las invitaciones del usuario."""
    make_user(111)
    make_user(222)
    client.post("/api/invitations", headers=auth_headers(111))

    response = client.get("/api/invitations", headers=auth_headers(111))
    other = client.get("/api/invitations", headers=auth_headers(222))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert other.json() == []
