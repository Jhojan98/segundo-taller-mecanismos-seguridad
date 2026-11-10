"""Pruebas de autorizaciones: creación, listado y revocación."""
import pytest

from app.services import authorization_service, invitation_service, user_service
from app.utils.exceptions import PermissionDeniedError


def _link(db, owner, guest):
    """Vincula dos usuarios creando y canjeando una invitación."""
    invitation = invitation_service.create(db, owner.id)
    invitation_service.redeem(db, invitation.codigo, guest.id)


def test_grant_creates_active_authorization(db, make_user):
    """Otorgar consentimiento deja la autorización en estado `activa`."""
    owner = make_user(1)
    viewer = make_user(2)

    auth = authorization_service.grant(db, owner.id, viewer.id)

    assert auth.estado == "activa"
    assert auth.fecha_autorizacion is not None
    assert auth.fecha_revocacion is None
    assert authorization_service.can_view(db, viewer.id, owner.id) is True


def test_grant_is_idempotent(db, make_user):
    """Volver a autorizar no duplica la relación (unicidad propietario-autorizado)."""
    owner = make_user(1)
    viewer = make_user(2)

    first = authorization_service.grant(db, owner.id, viewer.id)
    second = authorization_service.grant(db, owner.id, viewer.id)

    assert first.id == second.id


def test_revoke_only_allowed_for_owner(db, make_user):
    """Solo el propietario de la ubicación puede revocar su autorización."""
    owner = make_user(1)
    viewer = make_user(2)
    auth = authorization_service.grant(db, owner.id, viewer.id)

    with pytest.raises(PermissionDeniedError):
        authorization_service.revoke(db, auth.id, viewer.id)

    revoked = authorization_service.revoke(db, auth.id, owner.id)
    assert revoked.estado == "revocada"
    assert revoked.fecha_revocacion is not None
    assert authorization_service.can_view(db, viewer.id, owner.id) is False


def test_list_for_reports_both_roles(db, make_user):
    """Cada usuario ve las autorizaciones donde participa, con su rol."""
    owner = make_user(1)
    viewer = make_user(2)
    authorization_service.grant(db, owner.id, viewer.id)

    owner_rows = authorization_service.list_for(db, owner.id)
    viewer_rows = authorization_service.list_for(db, viewer.id)

    assert len(owner_rows) == 1
    assert owner_rows[0][1] == "propietario"
    assert owner_rows[0][2].id == viewer.id
    assert len(viewer_rows) == 1
    assert viewer_rows[0][1] == "autorizado"
    assert viewer_rows[0][2].id == owner.id


def test_api_list_authorizations(client, db, auth_headers, make_user):
    """`GET /api/authorizations` devuelve las autorizaciones del usuario."""
    owner = make_user(1, username="dueno")
    viewer = make_user(2, username="observador")
    _link(db, owner, viewer)
    authorization_service.grant(db, owner.id, viewer.id)

    response = client.get("/api/authorizations", headers=auth_headers(1))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["estado"] == "activa"
    assert payload[0]["rol"] == "propietario"
    assert payload[0]["usuario"]["telegram_id"] == 2


def test_api_create_authorization_requires_previous_link(client, db, auth_headers, make_user):
    """No se puede autorizar a un usuario con el que no existe vinculación."""
    owner = make_user(1)
    stranger = make_user(2)

    response = client.post(
        "/api/authorizations",
        json={"usuario_id": stranger.id},
        headers=auth_headers(1),
    )

    assert response.status_code == 422
    assert "vincularte" in response.json()["detail"]


def test_api_create_and_revoke_authorization(client, db, auth_headers, make_user):
    """Flujo completo por API: vincular, autorizar y revocar."""
    owner = make_user(1)
    viewer = make_user(2)
    _link(db, owner, viewer)

    created = client.post(
        "/api/authorizations",
        json={"usuario_id": viewer.id},
        headers=auth_headers(1),
    )
    assert created.status_code == 201
    auth_id = created.json()["id"]
    assert created.json()["estado"] == "activa"

    # El consultante ya puede ver la ubicación
    from app.services import location_service

    location_service.record(db, owner.id, 4.7110, -74.0721, None)
    history = client.get(f"/api/locations/history/{owner.id}", headers=auth_headers(2))
    assert history.status_code == 200

    # El propietario revoca y el acceso desaparece
    revoked = client.delete(f"/api/authorizations/{auth_id}", headers=auth_headers(1))
    assert revoked.status_code == 200
    assert revoked.json()["estado"] == "revocada"

    history_after = client.get(f"/api/locations/history/{owner.id}", headers=auth_headers(2))
    assert history_after.status_code == 403


def test_api_cannot_revoke_others_authorization(client, db, auth_headers, make_user):
    """El autorizado no puede revocar la autorización que lo favorece."""
    owner = make_user(1)
    viewer = make_user(2)
    _link(db, owner, viewer)
    created = client.post(
        "/api/authorizations",
        json={"usuario_id": viewer.id},
        headers=auth_headers(1),
    )
    auth_id = created.json()["id"]

    response = client.delete(f"/api/authorizations/{auth_id}", headers=auth_headers(2))

    assert response.status_code == 403


def test_api_cannot_authorize_self(client, db, auth_headers, make_user):
    """No se puede crear una autorización hacia uno mismo."""
    owner = make_user(1)

    response = client.post(
        "/api/authorizations",
        json={"usuario_id": owner.id},
        headers=auth_headers(1),
    )

    assert response.status_code == 422


def test_contacts_endpoint_reports_permissions(client, db, auth_headers, make_user):
    """`GET /api/users` lista contactos vinculados con el estado de permisos."""
    owner = make_user(1, username="dueno")
    viewer = make_user(2, username="observador")
    _link(db, owner, viewer)

    response = client.get("/api/users", headers=auth_headers(1))
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["usuario"]["telegram_id"] == 2
    assert payload[0]["puede_ver_mi_ubicacion"] is False
    assert payload[0]["puede_ver_su_ubicacion"] is False

    authorization_service.grant(db, owner.id, viewer.id)
    response_after = client.get("/api/users", headers=auth_headers(1)).json()
    assert response_after[0]["puede_ver_mi_ubicacion"] is True

    # El otro usuario también lo ve como contacto
    other_view = client.get("/api/users", headers=auth_headers(2)).json()
    assert len(other_view) == 1
    assert other_view[0]["usuario"]["telegram_id"] == 1
