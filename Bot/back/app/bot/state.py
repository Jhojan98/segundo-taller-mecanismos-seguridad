"""Estado compartido del bot de Telegram dentro del proceso backend."""
from typing import Literal

BotStatus = Literal["running", "disabled", "error"]

_STATUS: BotStatus = "disabled"


def set_status(status: BotStatus) -> None:
    """Actualiza el estado global del bot (lo usa el ciclo de vida de FastAPI)."""
    global _STATUS
    _STATUS = status


def get_status() -> str:
    """Devuelve el estado actual del bot: running | disabled | error."""
    return _STATUS
