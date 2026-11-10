"""Pruebas de construcción del bot (sin conexión con Telegram)."""
from telegram import KeyboardButton, ReplyKeyboardMarkup

from app.bot import keyboards, texts
from app.bot.application import build_application


def test_build_application_registers_handlers():
    """La aplicación del bot se construye y registra todos los manejadores."""
    application = build_application("123456:TEST-TOKEN-NO-REAL")

    assert application.updater is not None
    total_handlers = sum(len(handlers) for handlers in application.handlers.values())
    # 11 comandos + ubicación + contacto + texto + callback + comando desconocido
    assert total_handlers >= 15


def test_main_menu_requests_location_explicitly():
    """El menú usa `request_location=True` (consentimiento del usuario)."""
    markup = keyboards.main_menu()
    assert isinstance(markup, ReplyKeyboardMarkup)

    buttons = [button for row in markup.keyboard for button in row]
    location_buttons = [b for b in buttons if isinstance(b, KeyboardButton) and b.request_location]
    assert len(location_buttons) >= 1


def test_help_text_documents_limits():
    """La ayuda informa los límites reales del sistema."""
    help_text = texts.help_text()
    assert "no puede obtener tu GPS sin que tú envíes la ubicación" in help_text
    assert "No se pueden localizar números telefónicos arbitrarios" in help_text


def test_location_received_message_handles_missing_accuracy():
    """Cuando no hay precisión se informa como no informada (no se inventa)."""
    from app.models import Location

    location = Location(usuario_id=1, latitud=4.7110, longitud=-74.0721, precision=None)
    message = texts.location_received(location)

    assert "Precisión: no informada" in message


# --------------------------------------------------------------------------- #
# Regresión: el manejador debe funcionar con un `Location` REAL de PTB
# --------------------------------------------------------------------------- #
def _send_real_location(horizontal_accuracy: float | None):
    """Ejecuta `on_location` con un `telegram.Location` real (no un doble)."""
    import asyncio
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock, patch

    from telegram import Chat, Location, Message, Update, User

    from app.bot import handlers

    telegram_user = User(id=900001, first_name="Ana", is_bot=False)
    chat = Chat(id=900001, type="private")
    kwargs = {} if horizontal_accuracy is None else {"horizontal_accuracy": horizontal_accuracy}
    location = Location(longitude=-74.0721, latitude=4.7110, **kwargs)
    message = Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=chat,
        from_user=telegram_user,
        location=location,
    )
    update = Update(update_id=1, message=message)

    with patch.object(Message, "reply_text", new_callable=AsyncMock) as reply:
        asyncio.run(handlers.on_location(update, None))
        return reply


def test_on_location_accepts_real_telegram_location(db, make_user):
    """Guarda la ubicación usando `horizontal_accuracy` (PTB ≥ 20).

    Regresión: el código usaba `location.accuracy`, atributo inexistente en
    python-telegram-bot 22.x, y el envío real de ubicación fallaba en vivo.
    """
    from sqlalchemy import select

    from app.models import Location

    make_user(900001, username="ana")

    reply = _send_real_location(horizontal_accuracy=12.5)

    reply.assert_awaited_once()
    assert "✅" in reply.await_args.args[0]
    assert "Precisión: 12.5 m" in reply.await_args.args[0]

    rows = db.execute(select(Location)).scalars().all()
    assert len(rows) == 1
    assert rows[0].precision == 12.5


def test_on_location_without_accuracy_stores_none(db, make_user):
    """Si Telegram no informa precisión, se guarda `None` (no se inventa)."""
    from sqlalchemy import select

    from app.models import Location

    make_user(900001, username="ana")

    reply = _send_real_location(horizontal_accuracy=None)

    reply.assert_awaited_once()
    assert "Precisión: no informada" in reply.await_args.args[0]

    rows = db.execute(select(Location)).scalars().all()
    assert len(rows) == 1
    assert rows[0].precision is None


# --------------------------------------------------------------------------- #
# Regresión: Telegram rechaza `localhost` en botones inline (`wrong http url`)
# --------------------------------------------------------------------------- #
def test_url_button_rejects_localhost():
    """`url_button` no crea botón para URLs que Telegram rechazaría."""
    from telegram import InlineKeyboardMarkup

    assert keyboards.url_button("Abrir", "http://localhost:3000") is None
    assert keyboards.url_button("Abrir", "http://127.0.0.1:3000") is None
    assert keyboards.url_button("Abrir", "ftp://ejemplo.com") is None
    assert isinstance(keyboards.url_button("Abrir", "https://ejemplo.com"), InlineKeyboardMarkup)


def test_map_message_falls_back_to_text_with_localhost_url(monkeypatch):
    """Con `frontend_url` local, el mapa se envía como texto (sin botón).

    Regresión: el botón inline con `http://localhost:3000` hacía que
    Telegram respondiera `BadRequest: wrong http url` y el manejador fallara.
    """
    import asyncio
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock, patch

    from telegram import Chat, Message, User

    from app.bot import handlers
    from app.config import settings

    monkeypatch.setattr(settings, "frontend_url", "http://localhost:3000")

    message = Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=Chat(id=900001, type="private"),
        from_user=User(id=900001, first_name="Ana", is_bot=False),
    )

    with patch.object(Message, "reply_text", new_callable=AsyncMock) as reply:
        asyncio.run(handlers._do_map(message))

    reply.assert_awaited_once()
    text = reply.await_args.args[0]
    kwargs = reply.await_args.kwargs
    assert "http://localhost:3000" in text  # el enlace sigue disponible
    assert kwargs.get("reply_markup") is None  # pero sin botón inline
