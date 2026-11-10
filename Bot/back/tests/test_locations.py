"""Pruebas de registro y consulta de ubicaciones con control de permisos."""
import pytest

from app.services import authorization_service, config_service, location_service
from app.utils.exceptions import InvalidInputError, PermissionDeniedError

LAT, LON = 4.7110, -74.0721  # coordenadas usadas únicamente en pruebas


def test_record_location(db, make_user):
    """Almacena coordenadas, precisión y activa la compartición."""
    user = make_user(1)

    location = location_service.record(db, user.id, LAT, LON, 12.5)

    assert location.latitud == pytest.approx(LAT)
    assert location.longitud == pytest.approx(LON)
    assert location.precision == pytest.approx(12.5)
    assert location.fecha_hora is not None
    # Enviar una ubicación implica consentimiento explícito
    assert config_service.get(db, user.id).compartir_ubicacion is True


def test_record_location_without_accuracy(db, make_user):
    """Si Telegram no informa precisión, se almacena `NULL` (None)."""
    user = make_user(1)

    location = location_service.record(db, user.id, LAT, LON, None)

    assert location.precision is None


def test_record_location_rejects_invalid_coordinates(db, make_user):
    """Las coordenadas fuera de rango se rechazan."""
    user = make_user(1)

    with pytest.raises(InvalidInputError):
        location_service.record(db, user.id, 91.0, 0.0)
    with pytest.raises(InvalidInputError):
        location_service.record(db, user.id, 0.0, 181.0)


def test_own_locations_endpoint(client, db, auth_headers, make_user):
    """`GET /api/locations/me` devuelve el historial propio."""
    user = make_user(111, username="ana")
    location_service.record(db, user.id, LAT, LON, None)

    response = client.get("/api/locations/me", headers=auth_headers(111))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["latitud"] == pytest.approx(LAT)
    assert payload[0]["longitud"] == pytest.approx(LON)
    assert payload[0]["precision"] is None
    # La fecha se serializa en UTC con sufijo Z para el navegador
    assert payload[0]["fecha_hora"].endswith("Z")


def test_shared_locations_empty_without_authorization(client, db, auth_headers, make_user):
    """Sin autorización no se entrega ninguna ubicación de terceros."""
    owner = make_user(1, username="dueno")
    viewer = make_user(2, username="observador")
    location_service.record(db, owner.id, LAT, LON, 10)

    headers = auth_headers(viewer.telegram_id)
    shared = client.get("/api/locations/shared", headers=headers)
    history = client.get(f"/api/locations/history/{owner.id}", headers=headers)
    latest = client.get(f"/api/locations/latest/{owner.id}", headers=headers)

    assert shared.status_code == 200
    assert shared.json() == []
    assert history.status_code == 403
    assert latest.status_code == 403


def test_shared_locations_with_authorization(client, db, auth_headers, make_user):
    """Con autorización vigente el consultante recibe las ubicaciones."""
    owner = make_user(1, username="dueno")
    viewer = make_user(2, username="observador")
    location_service.record(db, owner.id, LAT, LON, 10)
    authorization_service.grant(db, propietario_id=owner.id, autorizado_id=viewer.id)

    headers = auth_headers(viewer.telegram_id)
    shared = client.get("/api/locations/shared", headers=headers)
    history = client.get(f"/api/locations/history/{owner.id}", headers=headers)
    latest = client.get(f"/api/locations/latest/{owner.id}", headers=headers)

    assert shared.status_code == 200
    payload = shared.json()
    assert len(payload) == 1
    assert payload[0]["usuario"]["telegram_id"] == owner.telegram_id
    assert payload[0]["ubicacion"]["latitud"] == pytest.approx(LAT)

    assert history.status_code == 200
    assert len(history.json()) == 1

    assert latest.status_code == 200
    assert latest.json()["longitud"] == pytest.approx(LON)


def test_pending_authorization_blocks_access(client, db, auth_headers, make_user):
    """Una autorización pendiente (sin consentimiento) no da acceso."""
    owner = make_user(1)
    viewer = make_user(2)
    location_service.record(db, owner.id, LAT, LON, None)
    authorization_service.create_pending(db, owner.id, viewer.id)

    response = client.get(f"/api/locations/history/{owner.id}", headers=auth_headers(2))

    assert response.status_code == 403


def test_revoked_authorization_blocks_access(client, db, auth_headers, make_user):
    """Tras revocar, el consultante pierde el acceso de inmediato."""
    owner = make_user(1)
    viewer = make_user(2)
    location_service.record(db, owner.id, LAT, LON, None)
    auth = authorization_service.grant(db, owner.id, viewer.id)
    headers = auth_headers(2)

    assert client.get(f"/api/locations/history/{owner.id}", headers=headers).status_code == 200

    authorization_service.revoke(db, auth.id, owner.id)

    assert client.get(f"/api/locations/history/{owner.id}", headers=headers).status_code == 403
    assert client.get("/api/locations/shared", headers=headers).json() == []


def test_owner_stops_sharing_hides_locations(client, db, auth_headers, make_user):
    """Detener la compartición oculta las ubicaciones pese a la autorización."""
    owner = make_user(1)
    viewer = make_user(2)
    location_service.record(db, owner.id, LAT, LON, None)
    authorization_service.grant(db, owner.id, viewer.id)
    headers = auth_headers(2)

    assert client.get("/api/locations/shared", headers=headers).json() != []

    config_service.set_sharing(db, owner.id, False)

    assert client.get("/api/locations/shared", headers=headers).json() == []
    assert client.get(f"/api/locations/history/{owner.id}", headers=headers).status_code == 403


def test_owner_can_always_query_own_locations(client, db, auth_headers, make_user):
    """El propietario consulta su propio historial sin autorizaciones."""
    owner = make_user(1)
    location_service.record(db, owner.id, LAT, LON, None)
    config_service.set_sharing(db, owner.id, False)

    response = client.get(f"/api/locations/history/{owner.id}", headers=auth_headers(1))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_purge_older_than_applies_retention(db, make_user):
    """La política de retención elimina ubicaciones antiguas."""
    from datetime import timedelta

    from app.models import Location
    from app.utils.dates import utcnow

    user = make_user(1)
    location_service.record(db, user.id, LAT, LON, None)
    location_service.record(db, user.id, LAT, LON, None)
    # Se envejece manualmente una ubicación
    old = db.query(Location).order_by(Location.id.desc()).first()
    old.fecha_hora = utcnow() - timedelta(days=90)
    db.commit()

    removed = location_service.purge_older_than(db, days=30)

    assert removed == 1
    assert location_service.count_for(db, user.id) == 1
