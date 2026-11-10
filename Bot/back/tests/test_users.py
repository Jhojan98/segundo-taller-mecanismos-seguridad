"""Pruebas de registro de usuarios y del endpoint `/api/users/me`."""
from sqlalchemy import func, select

from app.models import User
from app.services import user_service


def test_register_user(db):
    """`/start` registra al usuario por primera vez."""
    user, created = user_service.get_or_create(db, telegram_id=111, username="ana", nombre="Ana")

    assert created is True
    assert user.telegram_id == 111
    assert user.estado == "activo"
    assert user.fecha_registro is not None


def test_no_duplicate_users_by_telegram_id(db):
    """Un segundo `/start` con el mismo `telegram_id` no duplica el registro."""
    first, created_first = user_service.get_or_create(db, telegram_id=111, username="ana")
    second, created_second = user_service.get_or_create(db, telegram_id=111, username="ana")

    total = db.scalar(select(func.count(User.id)))
    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert total == 1


def test_update_visible_profile_data(db):
    """Si cambian el nombre o el username de Telegram, se actualizan sin duplicar."""
    user, _ = user_service.get_or_create(db, telegram_id=222, username="old", nombre="Antiguo")
    updated, created = user_service.get_or_create(db, telegram_id=222, username="new", nombre="Nuevo")

    assert created is False
    assert updated.id == user.id
    assert updated.username == "new"
    assert updated.nombre == "Nuevo"


def test_users_me_requires_authentication(client):
    """Los endpoints protegidos rechazan peticiones sin token."""
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_users_me_returns_authenticated_identity(client, auth_headers, make_user):
    """El usuario devuelto proviene del token, no de un parámetro del cliente."""
    make_user(111, username="ana", nombre="Ana")
    response = client.get("/api/users/me", headers=auth_headers(111))

    assert response.status_code == 200
    payload = response.json()
    assert payload["telegram_id"] == 111
    assert payload["username"] == "ana"


def test_users_me_rejects_invalid_token(client):
    """Un token manipulado no autentica a nadie."""
    response = client.get("/api/users/me", headers={"Authorization": "Bearer token-falso"})
    assert response.status_code == 401
