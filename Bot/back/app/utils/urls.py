"""Validación de direcciones para botones inline de Telegram.

El Bot API de Telegram rechaza con ``wrong http url`` las direcciones que no
son HTTP(S) válidas y públicas: por ejemplo ``http://localhost:3000`` no puede
usarse en un botón inline (aunque sí como enlace en el texto de un mensaje).

Cuando la URL del panel no es apta para un botón, el envía el enlace como
texto plano para que la funcionalidad siga disponible en local.
"""
from urllib.parse import urlparse


def is_valid_telegram_button_url(url: str) -> bool:
    """`True` si Telegram aceptaría `url` como botón inline.

    Descarta esquemas distintos de http/https, direcciones sin host y
    destinos de solo uso local (`localhost`, `127.0.0.0/8`, `::1`,
    `0.0.0.0`), que el Bot API valida como URL pública.
    """
    try:
        parsed = urlparse(url or "")
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    host = (parsed.hostname or "").lower()
    if not host:
        return False
    if host == "localhost" or host == "::1" or host == "0.0.0.0":
        return False
    if host.startswith("127."):  # 127.0.0.0/8
        return False
    return True
