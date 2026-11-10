"""Mensajes en español utilizados por el bot de Telegram."""
from datetime import datetime

from app.config import settings
from app.models import Authorization, Invitation, Location, User
from app.utils.dates import to_iso_utc


def _nombre(user: User | None) -> str:
    if user is None:
        return "usuario"
    if user.nombre:
        return user.nombre
    if user.username:
        return f"@{user.username}"
    return f"usuario {user.telegram_id}"


def welcome_new(user: User) -> str:
    return (
        f"👋 ¡Hola, {_nombre(user)}! Tu cuenta ha sido registrada.\n\n"
        "Este bot te permite compartir tu ubicación de forma **voluntaria** con "
        "persones que autorices explícitamente.\n\n"
        "Comandos disponibles: /menu /ayuda"
    )


def welcome_back(user: User) -> str:
    return f"👋 ¡Bienvenido de nuevo, {_nombre(user)}! Usa /menu para ver las opciones."


def main_menu_help() -> str:
    return (
        "📌 Menú principal\n\n"
        "• 📍 Compartir ubicación: envía tu posición actual.\n"
        "• 🗺️ Consultar mapa: abre el panel web con tu mapa.\n"
        "• 👥 Mis contactos: personas vinculadas.\n"
        "• 🔐 Permisos: quién puede ver tu ubicación y de quién.\n"
        "• 🕘 Historial: tus ubicaciones registradas.\n"
        "• 🛑 Detener compartición: deja de compartir tu ubicación.\n\n"
        "Otros comandos: /vincular /compartir /mis_ubicaciones /contactos "
        "/permisos /detener /web /ayuda"
    )


def invitation_created(invitation: Invitation, minutes: int) -> str:
    return (
        "🔗 **Invitación generada**\n\n"
        f"Código: `{invitation.codigo}`\n"
        f"Válido durante {minutes} minutos y de un solo uso.\n\n"
        "La otra persona debe iniciar conversación con este bot y enviar:\n"
        f"`/vincular {invitation.codigo}`\n\n"
        "La relación quedará **pendiente** de tu autorización explícita."
    )


def link_done(owner: User) -> str:
    return (
        f"✅ Vinculación registrada con {_nombre(owner)}.\n"
        "Ahora espera a que esa persona autorice compartir su ubicación; tú "
        "podrás consultarla cuando lo haga."
    )


def authorization_request(requester: User) -> str:
    return (
        f"🔐 **Solicitud de vinculación**\n\n"
        f"{_nombre(requester)} canjeó tu invitación y solicita acceder a tu "
        "ubicación compartida.\n\n"
        "¿Autorizas compartir tu ubicación con esta persona?"
    )


def authorization_approved(owner: User, authorized: User) -> str:
    return (
        f"✅ {_nombre(owner)} autorizó compartir su ubicación contigo.\n"
        "Ya puedes consultarla desde el mapa web o con /contactos."
    )


def authorization_rejected(owner: User) -> str:
    return f"❌ {_nombre(owner)} rechazó la solicitud de vinculación."


def authorization_revoked(owner: User, other: User) -> str:
    return (
        f"🚫 {_nombre(owner)} revocó la autorización: ya no podrás consultar "
        "su ubicación."
    )


def share_prompt() -> str:
    return (
        "📍 **Compartir ubicación**\n\n"
        "Pulsa el botón de abajo y envía tu ubicación actual desde Telegram.\n\n"
        "⚠️ Solo se recibe lo que tú envías: el bot **no** accede a tu GPS en "
        "segundo plano ni puede rastrearte sin tu acción."
    )


def location_received(location: Location) -> str:
    precision_text = (
        f"{location.precision:g} m" if location.precision is not None else "no informada"
    )
    return (
        "✅ **Ubicación recibida y almacenada**\n\n"
        f"Latitud: `{location.latitud}`\n"
        f"Longitud: `{location.longitud}`\n"
        f"Precisión: {precision_text}\n"
        f"Fecha y hora (UTC): {to_iso_utc(location.fecha_hora)}\n\n"
        "Las personas autorizadas podrán verla en el mapa web.\n"
        "Usa /detener cuando quieras dejar de compartirla."
    )


def no_locations() -> str:
    return "ℹ️ Aún no has compartido ninguna ubicación. Usa /compartir para enviar tu primera."


def locations_summary(user: User, total: int, latest: Location | None, sharing: bool) -> str:
    estado = "✅ Compartiendo" if sharing else "🛑 Detenida"
    lines = [
        "🗂️ **Mis ubicaciones**",
        f"Total registradas: {total}",
        f"Estado: {estado}",
    ]
    if latest is not None:
        lines += [
            f"Última: `{latest.latitud}`, `{latest.longitud}`",
            f"Fecha (UTC): {to_iso_utc(latest.fecha_hora)}",
        ]
    else:
        lines.append("Última: sin datos")
    return "\n".join(lines)


def contacts_list(contacts: list[tuple[User, bool, bool]]) -> str:
    """`contacts`: (usuario, puede_ver_mi_ubicacion, puede_ver_su_ubicacion)."""
    if not contacts:
        return (
            "👥 No tienes contactos vinculados todavía.\n"
            "Genera un código con /vincular y pide a la otra persona que lo use."
        )
    lines = ["👥 **Mis contactos**"]
    for user, ve_mi, ve_su in contacts:
        flags = []
        flags.append("ve mi ubicación ✅" if ve_mi else "ve mi ubicación ❌")
        flags.append("yo veo la suya ✅" if ve_su else "yo veo la suya ❌")
        lines.append(f"• {_nombre(user)} — {', '.join(flags)}")
    return "\n".join(lines)


def permissions_list(
    i_can_see: list[tuple[Authorization, User]],
    they_can_see_me: list[tuple[Authorization, User]],
) -> str:
    lines = ["🔐 **Permisos**", "", "📍 Puedo ver la ubicación de:"]
    if i_can_see:
        lines += [f"• {_nombre(user)} ({auth.estado})" for auth, user in i_can_see]
    else:
        lines.append("  Nadie autorizado todavía.")
    lines.append("")
    lines.append("👁️ Pueden ver mi ubicación:")
    if they_can_see_me:
        lines += [f"• {_nombre(user)} ({auth.estado})" for auth, user in they_can_see_me]
    else:
        lines.append("  Nadie autorizado todavía.")
    return "\n".join(lines)


def stop_confirmation() -> str:
    return (
        "🛑 **Compartición detenida**\n\n"
        "Tus ubicaciones dejan de entregarse a terceros de inmediato, aunque "
        "conserven las autorizaciones.\n"
        "Vuelve a compartirla cuando quieras con /compartir."
    )


def already_stopped() -> str:
    return "ℹ️ La compartición de tu ubicación ya estaba detenida."


def share_enabled() -> str:
    return "✅ La compartición de tu ubicación está activa."


def map_message() -> str:
    return "🗺️ Abre el panel web para visualizar las ubicaciones autorizadas:"


def history_message(user: User, total: int) -> str:
    return (
        f"🕘 Tienes {total} ubicaciones registradas.\n"
        "Consulta el historial completo en el panel web (sección Historial)."
    )


def web_code(code: str, minutes: int) -> str:
    return (
        "🔑 **Código de acceso web**\n\n"
        f"Código: `{code}`\n"
        f"Válido durante {minutes} minutos y de un solo uso.\n\n"
        "Introdúcelo en la página del panel:\n"
        f"{settings.frontend_url}\n\n"
        "Este código demuestra que controlas esta cuenta de Telegram; no lo "
        "compartas con nadie."
    )


def help_text() -> str:
    return (
        "ℹ️ **Ayuda**\n\n"
        "Este sistema permite compartir tu ubicación de forma voluntaria con "
        "persones que autorices.\n\n"
        "**Comandos**\n"
        "/start — registrarse\n"
        "/menu — menú principal\n"
        "/vincular — generar código de invitación\n"
        "/vincular CODIGO — canjear un código recibido\n"
        "/compartir — enviar tu ubicación actual\n"
        "/mis_ubicaciones — resumen de tus ubicaciones\n"
        "/contactos — personas vinculadas\n"
        "/permisos — autorizaciones vigentes\n"
        "/detener — dejar de compartir tu ubicación\n"
        "/telefono — compartir (opcional) tu número\n"
        "/web — generar código de acceso al panel web\n"
        "/ayuda — esta ayuda\n\n"
        "**Límites importantes**\n"
        "• El bot no puede obtener tu GPS sin que tú envíes la ubicación.\n"
        "• No se pueden localizar números telefónicos arbitrarios.\n"
        "• Tu ubicación solo se muestra a quienes hayas autorizado."
    )


def phone_saved(telefono: str) -> str:
    return f"📱 Número guardado ({telefono}). Puedes retirarlo eliminando tus datos con el equipo del proyecto."


def phone_not_provided() -> str:
    return "ℹ️ No se recibió ningún número de contacto. Usa el botón de contacto para compartirlo (opcional)."


def generic_error() -> str:
    return "⚠️ Ocurrió un error inesperado. Inténtalo de nuevo o usa /ayuda."


def domain_error(message: str) -> str:
    return f"⚠️ {message}"


def unknown_command() -> str:
    return "❓ Comando no reconocido. Usa /menu para ver las opciones o /ayuda."


def not_registered() -> str:
    return "🔒 Primero debes registrarte: envía /start."


def format_datetime(value: datetime | None) -> str:
    return to_iso_utc(value) or "-"
