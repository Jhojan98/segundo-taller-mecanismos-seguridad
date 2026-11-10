"""Pruebas del endpoint de salud, del flujo de login web y de configuración."""
from datetime import timedelta

from app.services import auth_service, config_service, location_service
from app.utils.dates import utcnow


def test_health_reports_database_ok(client):
    """`GET /api/health` confirma que el backend y la BD responden."""
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    # En las pruebas el token de Telegram está vacío: el bot queda deshabilitado
    assert payload["bot"] == "disabled"
    assert payload["timestamp"].endswith("Z")


def test_web_login_flow(client, db, make_user):
    """Código de `/web` → JWT → identidad autenticada en la API."""
    user = make_user(111, username="ana", nombre="Ana")
    codigo = auth_service.create_web_code(db, user.id)

    login = client.post("/api/auth/token", json={"codigo": codigo})

    assert login.status_code == 200
    payload = login.json()
    assert payload["token_type"] == "bearer"
    assert payload["usuario"]["telegram_id"] == 111

    me = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["telegram_id"] == 111


def test_web_login_code_single_use(client, db, make_user):
    """El código de acceso no puede canjearse dos veces."""
    user = make_user(111)
    codigo = auth_service.create_web_code(db, user.id)

    first = client.post("/api/auth/token", json={"codigo": codigo})
    second = client.post("/api/auth/token", json={"codigo": codigo})

    assert first.status_code == 200
    assert second.status_code == 409


def test_web_login_invalid_code(client):
    """Un código inexistente no genera token."""
    response = client.post("/api/auth/token", json={"codigo": "ABCDEFGH"})
    assert response.status_code == 401


def test_web_login_expired_code(client, db, make_user):
    """Un código caducado no genera token."""
    from app.models import WebLoginCode

    user = make_user(111)
    codigo = auth_service.create_web_code(db, user.id)
    record = db.query(WebLoginCode).filter(WebLoginCode.codigo == codigo).one()
    record.fecha_expiracion = utcnow() - timedelta(minutes=1)
    db.commit()

    response = client.post("/api/auth/token", json={"codigo": codigo})
    assert response.status_code == 422


def test_config_endpoint_reports_and_updates_sharing(client, db, auth_headers, make_user):
    """`GET/PUT /api/config` controla el interruptor de compartición."""
    user = make_user(111)
    headers = auth_headers(111)

    initial = client.get("/api/config", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["compartir_ubicacion"] is False

    updated = client.put("/api/config", json={"compartir_ubicacion": True}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["compartir_ubicacion"] is True

    assert config_service.get(db, user.id).compartir_ubicacion is True


def test_shared_endpoint_empty_for_new_user(client, db, auth_headers, make_user):
    """Un usuario nuevo no recibe ubicaciones de terceros."""
    make_user(111)
    response = client.get("/api/locations/shared", headers=auth_headers(111))

    assert response.status_code == 200
    assert response.json() == []


def test_history_and_latest_return_null_without_location(client, db, auth_headers, make_user):
    """Con permiso y compartición activa pero sin ubicaciones: `latest` devuelve `null`."""
    from app.services import authorization_service

    owner = make_user(1)
    viewer = make_user(2)
    authorization_service.grant(db, owner.id, viewer.id)
    headers = auth_headers(2)

    # Regla de doble consentimiento: sin compartición activada no hay acceso
    assert client.get(f"/api/locations/latest/{owner.id}", headers=headers).status_code == 403

    config_service.set_sharing(db, owner.id, True)

    latest = client.get(f"/api/locations/latest/{owner.id}", headers=headers)
    assert latest.status_code == 200
    assert latest.json() is None
    # Y el historial viene vacío, no con datos ficticios
    history = client.get(f"/api/locations/history/{owner.id}", headers=headers)
    assert history.status_code == 200
    assert history.json() == []
    # Referencia de uso para evitar import no utilizado
    assert location_service.count_for(db, owner.id) == 0
