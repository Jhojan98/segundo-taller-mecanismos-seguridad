"""Construcción y ciclo de vida del bot dentro del proceso de FastAPI.

Se usa el patrón documentado por python-telegram-bot para "embeber" la
aplicación en otro framework: se inicializa, se inicia y se detiene junto con
el servidor, todo en el mismo bucle de eventos asyncio de Uvicorn.
"""
import logging

from telegram.ext import Application

from app.bot import handlers

logger = logging.getLogger(__name__)


def build_application(token: str) -> Application:
    """Crea la `Application` de PTB y registra todos los manejadores."""
    application = Application.builder().token(token).build()
    handlers.register_handlers(application)
    return application


async def start_bot(application: Application) -> None:
    """Arranca el bot en modo polling (sin webhook ni dominio público)."""
    if application.updater is None:  # pragma: no cover - defensa
        raise RuntimeError("La aplicación de Telegram no tiene Updater configurado")
    await application.initialize()
    await application.start()
    # `drop_pending_updates=True` evita procesar mensajes antiguos al reiniciar
    await application.updater.start_polling(drop_pending_updates=True)
    logger.info("Polling de Telegram activo")


async def stop_bot(application: Application) -> None:
    """Detiene el bot de forma ordenada al apagar el backend."""
    if application.updater is not None and application.updater.running:
        await application.updater.stop()
    if application.running:
        await application.stop()
    await application.shutdown()
