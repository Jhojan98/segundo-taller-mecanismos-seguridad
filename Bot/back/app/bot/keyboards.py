"""Teclados (markups) utilizados por el bot de Telegram."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.utils.urls import is_valid_telegram_button_url

# Textos de los botones del menú principal (coinciden con los de `texts`)
TEXT_SHARE = "📍 Compartir ubicación"
TEXT_MAP = "🗺️ Consultar mapa"
TEXT_CONTACTS = "👥 Mis contactos"
TEXT_PERMISSIONS = "🔐 Permisos"
TEXT_HISTORY = "🕘 Historial"
TEXT_STOP = "🛑 Detener compartición"
TEXT_MENU = "🔙 Menú"


def main_menu() -> ReplyKeyboardMarkup:
    """Menú principal persistente.

    El botón de ubicación usa `request_location=True`: Telegram mostrará el
    selector nativo de ubicación y solo enviará las coordenadas si el usuario
    lo confirma (consentimiento explícito).
    """
    keyboard = [
        [KeyboardButton(TEXT_SHARE, request_location=True), KeyboardButton(TEXT_MAP)],
        [KeyboardButton(TEXT_CONTACTS), KeyboardButton(TEXT_PERMISSIONS)],
        [KeyboardButton(TEXT_HISTORY), KeyboardButton(TEXT_STOP)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def location_request() -> ReplyKeyboardMarkup:
    """Teclado enfocado en el envío de la ubicación actual."""
    keyboard = [
        [KeyboardButton("📍 Enviar mi ubicación actual", request_location=True)],
        [KeyboardButton(TEXT_MENU)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def contact_request() -> ReplyKeyboardMarkup:
    """Teclado para compartir el número telefónico (opcional y voluntario)."""
    keyboard = [
        [KeyboardButton("📱 Compartir mi número de contacto", request_contact=True)],
        [KeyboardButton(TEXT_MENU)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def authorization_request(auth_id: int) -> InlineKeyboardMarkup:
    """Botones para que el propietario apruebe o rechace una vinculación."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Autorizar", callback_data=f"auth:ok:{auth_id}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"auth:no:{auth_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def revoke_buttons(auth_ids: list[int]) -> InlineKeyboardMarkup | None:
    """Botones de revocación (máximo 8 por mensaje, límite de Telegram)."""
    if not auth_ids:
        return None
    keyboard = [
        [InlineKeyboardButton(f"🚫 Revocar #{auth_id}", callback_data=f"auth:rev:{auth_id}")]
        for auth_id in auth_ids[:8]
    ]
    return InlineKeyboardMarkup(keyboard)


def url_button(text: str, url: str) -> InlineKeyboardMarkup | None:
    """Botón que abre una dirección web (por ejemplo, el mapa).

    Devuelve `None` si Telegram no aceptaría la URL en un botón inline
    (p. ej. `http://localhost:3000`): el mensaje debe enviarse con el
    enlace como texto plano.
    """
    if not is_valid_telegram_button_url(url):
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, url=url)]])
