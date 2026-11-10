"""Manejadores de comandos, mensajes y callbacks del bot de Telegram.

Todos los manejadores trabajan sobre conversaciones privadas (el bot ignora los
mensajes de grupos) y abren su propia sesión de base de datos, que se cierra
al terminar la operación.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine

from telegram import Message, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.bot import keyboards, texts
from app.config import settings
from app.database import SessionLocal
from app.services import (
    authorization_service,
    auth_service,
    config_service,
    invitation_service,
    location_service,
    user_service,
)
from app.utils import exceptions
from app.utils.exceptions import DomainError

logger = logging.getLogger(__name__)


def with_db(handler: Callable[..., Coroutine[Any, Any, None]]) -> Callable[..., Coroutine[Any, Any, None]]:
    """Decorador que gestiona la sesión de BD y los errores de cada manejador."""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        db = SessionLocal()
        try:
            await handler(update, context, db)
        except DomainError as exc:
            logger.info("Rechazo de dominio en %s: %s", handler.__name__, exc.message)
            if message is not None:
                await message.reply_text(texts.domain_error(exc.message))
        except Exception:  # noqa: BLE001 - nunca se filtran detalles internos
            logger.exception("Error inesperado en %s", handler.__name__)
            if message is not None:
                await message.reply_text(texts.generic_error())
        finally:
            db.close()

    # Se copian solo metadatos (sin `__wrapped__`) para no alterar la
    # introspección que hace python-telegram-bot sobre los manejadores.
    wrapper.__name__ = handler.__name__
    wrapper.__doc__ = handler.__doc__
    return wrapper


def _ctx(update: Update) -> tuple[Message, Any, Any] | None:
    """Devuelve (mensaje, chat, usuario) solo en conversaciones privadas."""
    message = update.effective_message
    chat = update.effective_chat
    tg_user = update.effective_user
    if message is None or chat is None or tg_user is None:
        return None
    if chat.type != "private":
        return None
    return message, chat, tg_user


def _get_user(db, tg_user) -> Any | None:
    """Usuario registrado (o `None` si aún no usó /start)."""
    return user_service.get_by_telegram_id(db, tg_user.id)


async def _notify(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, reply_markup=None) -> None:
    """Envía un mensaje privado, registrando el error si el bot fue bloqueado."""
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    except Exception:  # noqa: BLE001 - el usuario pudo bloquear al bot
        logger.warning("No fue posible notificar al chat %s", chat_id)


# --------------------------------------------------------------------------- #
# Acciones compartidas entre comandos y botones del menú
# --------------------------------------------------------------------------- #

async def _show_menu(message: Message) -> None:
    await message.reply_text(texts.main_menu_help(), reply_markup=keyboards.main_menu())


async def _do_share(message: Message) -> None:
    await message.reply_text(texts.share_prompt(), reply_markup=keyboards.location_request())


async def _do_map(message: Message) -> None:
    markup = keyboards.url_button("🗺️ Abrir el panel web", settings.frontend_url)
    if markup is None:
        # `localhost` no es válida en botones inline de Telegram: se envía
        # el enlace como texto para no perder la funcionalidad en local.
        await message.reply_text(f"{texts.map_message()}\n{settings.frontend_url}")
        return
    await message.reply_text(texts.map_message(), reply_markup=markup)


async def _do_history(message: Message, db, user) -> None:
    total = location_service.count_for(db, user.id)
    text = texts.history_message(user, total)
    markup = keyboards.url_button("🕘 Ver historial en el web", settings.frontend_url)
    if markup is None:
        await message.reply_text(f"{text}\n{settings.frontend_url}")
        return
    await message.reply_text(text, reply_markup=markup)


async def _do_contacts(message: Message, db, user) -> None:
    items = []
    for other, _linked_at in user_service.list_contacts(db, user.id):
        ve_mi = authorization_service.get_active(db, user.id, other.id) is not None
        ve_su = authorization_service.get_active(db, other.id, user.id) is not None
        items.append((other, ve_mi, ve_su))
    await message.reply_text(texts.contacts_list(items), reply_markup=keyboards.main_menu())


async def _do_permissions(message: Message, db, user) -> None:
    rows = authorization_service.list_for(db, user.id)
    i_can_see = [(a, other) for a, role, other in rows if role == "autorizado" and a.estado == "activa"]
    they_can_see = [
        (a, other)
        for a, role, other in rows
        if role == "propietario" and a.estado in ("activa", "pendiente")
    ]
    revoke_ids = [a.id for a, _other in they_can_see if a.estado == "activa"]
    await message.reply_text(
        texts.permissions_list(i_can_see, they_can_see),
        reply_markup=keyboards.revoke_buttons(revoke_ids) or keyboards.main_menu(),
    )


async def _do_stop(message: Message, db, user) -> None:
    config = config_service.get(db, user.id)
    if not config.compartir_ubicacion:
        await message.reply_text(texts.already_stopped(), reply_markup=keyboards.main_menu())
        return
    config_service.set_sharing(db, user.id, False)
    await message.reply_text(texts.stop_confirmation(), reply_markup=keyboards.main_menu())


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #

@with_db
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Registra al usuario o lo reconoce sin duplicarlo."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user, created = user_service.get_or_create(
        db,
        telegram_id=tg_user.id,
        username=tg_user.username,
        nombre=tg_user.first_name,
    )
    if created:
        await message.reply_text(texts.welcome_new(user))
    else:
        await message.reply_text(texts.welcome_back(user))
    await _show_menu(message)


@with_db
async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Muestra el menú principal con botones."""
    ctx = _ctx(update)
    if ctx is None:
        return
    await _show_menu(ctx[0])


@with_db
async def cmd_vincular(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Genera un código de invitación o canjea uno recibido."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return

    args = context.args or []
    if not args:
        invitation = invitation_service.create(db, user.id)
        await message.reply_text(
            texts.invitation_created(invitation, settings.invitation_expire_minutes)
        )
        return

    invitation, authorization = invitation_service.redeem(db, args[0], user.id)
    owner = user_service.get_by_id(db, invitation.usuario_emisor_id)
    await message.reply_text(texts.link_done(owner))
    # Se solicita el consentimiento explícito del propietario
    await _notify(
        context,
        owner.telegram_id,
        texts.authorization_request(user),
        reply_markup=keyboards.authorization_request(authorization.id),
    )


@with_db
async def cmd_compartir(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Solicita al usuario que envíe su ubicación actual."""
    ctx = _ctx(update)
    if ctx is None:
        return
    await _do_share(ctx[0])


@with_db
async def on_location(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Recibe y almacena la ubicación enviada voluntariamente por el usuario."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    location = message.location
    if location is None:
        return

    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return

    stored = location_service.record(
        db,
        user_id=user.id,
        latitud=location.latitude,
        longitud=location.longitude,
        precision=location.horizontal_accuracy,  # None si Telegram no lo informa
    )
    await message.reply_text(texts.location_received(stored), reply_markup=keyboards.main_menu())


@with_db
async def cmd_mis_ubicaciones(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Resumen de las ubicaciones del usuario y su estado de compartición."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return
    total = location_service.count_for(db, user.id)
    latest = location_service.latest_own(db, user.id)
    sharing = config_service.get(db, user.id).compartir_ubicacion
    await message.reply_text(
        texts.locations_summary(user, total, latest, sharing),
        reply_markup=keyboards.main_menu(),
    )


@with_db
async def cmd_contactos(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Lista los usuarios vinculados y el estado de los permisos mutuos."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return
    await _do_contacts(message, db, user)


@with_db
async def cmd_permisos(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Muestra las autorizaciones vigentes con botones de revocación."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return
    await _do_permissions(message, db, user)


@with_db
async def cmd_detener(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Detiene la compartición de la ubicación del usuario."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return
    await _do_stop(message, db, user)


@with_db
async def cmd_web(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Genera un código de un solo uso para iniciar sesión en el panel web."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return
    codigo = auth_service.create_web_code(db, user.id)
    await message.reply_text(texts.web_code(codigo, settings.web_code_expire_minutes))


@with_db
async def cmd_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Ofrece compartir el número telefónico (opcional y voluntario)."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return
    await message.reply_text(
        "📱 Puedes compartir tu número de forma **opcional** con el botón de "
        "contacto. No es necesario para usar el sistema.",
        reply_markup=keyboards.contact_request(),
    )


@with_db
async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Muestra las instrucciones de uso."""
    ctx = _ctx(update)
    if ctx is None:
        return
    await ctx[0].reply_text(texts.help_text(), reply_markup=keyboards.main_menu())


@with_db
async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Almacena el número telefónico solo si el usuario lo comparte voluntariamente."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    contact = message.contact
    if contact is None:
        return
    if contact.user_id and contact.user_id != tg_user.id:
        await message.reply_text("⚠️ Solo puedes compartir tu propio número de contacto.")
        return

    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return
    user_service.set_telefono(db, user, contact.phone_number)
    await message.reply_text(texts.phone_saved(contact.phone_number), reply_markup=keyboards.main_menu())


@with_db
async def on_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Procesa los botones de texto del menú principal."""
    ctx = _ctx(update)
    if ctx is None:
        return
    message, _chat, tg_user = ctx
    text = (message.text or "").strip()

    if text == keyboards.TEXT_SHARE:
        await _do_share(message)
        return
    if text == keyboards.TEXT_MAP:
        await _do_map(message)
        return
    if text == keyboards.TEXT_MENU:
        await _show_menu(message)
        return

    user = _get_user(db, tg_user)
    if user is None:
        await message.reply_text(texts.not_registered())
        return

    if text == keyboards.TEXT_CONTACTS:
        await _do_contacts(message, db, user)
    elif text == keyboards.TEXT_PERMISSIONS:
        await _do_permissions(message, db, user)
    elif text == keyboards.TEXT_HISTORY:
        await _do_history(message, db, user)
    elif text == keyboards.TEXT_STOP:
        await _do_stop(message, db, user)
    else:
        await message.reply_text(
            "❓ No entendí ese mensaje. Usa /menu para ver las opciones.",
            reply_markup=keyboards.main_menu(),
        )


@with_db
async def on_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Atiende los botones inline: autorizar, rechazar y revocar."""
    query = update.callback_query
    if query is None or not query.data:
        return
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "auth":
        return
    action, raw_id = parts[1], parts[2]
    if not raw_id.isdigit():
        return
    auth_id = int(raw_id)

    tg_user = update.effective_user
    if tg_user is None:
        return
    user = _get_user(db, tg_user)
    if user is None:
        await query.edit_message_text(texts.not_registered())
        return

    authorization = authorization_service.get_by_id(db, auth_id)
    if authorization is None:
        await query.edit_message_text("ℹ️ La solicitud ya no está disponible.")
        return

    if action == "ok":
        authorization = authorization_service.approve(db, auth_id, user.id)
        other = user_service.get_by_id(db, authorization.autorizado_id)
        await _notify(
            context,
            other.telegram_id,
            texts.authorization_approved(user, other),
        )
        await query.edit_message_text("✅ Autorización concedida: esta persona podrá consultar tu ubicación.")

    elif action == "no":
        authorization = authorization_service.reject(db, auth_id, user.id)
        other = user_service.get_by_id(db, authorization.autorizado_id)
        await _notify(context, other.telegram_id, texts.authorization_rejected(user))
        await query.edit_message_text("❌ Solicitud rechazada.")

    elif action == "rev":
        authorization = authorization_service.revoke(db, auth_id, user.id)
        other = user_service.get_by_id(db, authorization.autorizado_id)
        await _notify(context, other.telegram_id, texts.authorization_revoked(user, other))
        await query.edit_message_text("🚫 Autorización revocada. Dejas de compartir tu ubicación.")


@with_db
async def on_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db) -> None:
    """Responde a comandos no reconocidos."""
    ctx = _ctx(update)
    if ctx is None:
        return
    await ctx[0].reply_text(texts.unknown_command(), reply_markup=keyboards.main_menu())


def register_handlers(application: Application) -> None:
    """Registra en orden todos los manejadores del bot.

    El orden importa: los comandos conocidos y el teclado principal se
    registran antes de los detectores genéricos.
    """
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("menu", cmd_menu))
    application.add_handler(CommandHandler("vincular", cmd_vincular))
    application.add_handler(CommandHandler("compartir", cmd_compartir))
    application.add_handler(CommandHandler("mis_ubicaciones", cmd_mis_ubicaciones))
    application.add_handler(CommandHandler("contactos", cmd_contactos))
    application.add_handler(CommandHandler("permisos", cmd_permisos))
    application.add_handler(CommandHandler("detener", cmd_detener))
    application.add_handler(CommandHandler("telefono", cmd_telefono))
    application.add_handler(CommandHandler("web", cmd_web))
    application.add_handler(CommandHandler("ayuda", cmd_ayuda))

    application.add_handler(MessageHandler(filters.LOCATION, on_location))
    application.add_handler(MessageHandler(filters.CONTACT, on_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_menu_text))
    application.add_handler(CallbackQueryHandler(on_callback_query))
    # Detectores genéricos al final
    application.add_handler(MessageHandler(filters.COMMAND, on_unknown_command))
