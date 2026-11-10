"""Aplicación FastAPI del MVP de ubicación compartida.

El backend expone la API REST y, dentro del mismo proceso, administra el ciclo
de vida del bot de Telegram (polling). De esta forma no se ejecutan dos
procesos independientes sin supervisión.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bot import state as bot_state
from app.bot.application import build_application, start_bot, stop_bot
from app.config import settings
from app.database import Base, engine
from app.routers import (
    auth,
    authorizations,
    config,
    health,
    invitations,
    locations,
    users,
)
from app.utils.exceptions import register_exception_handlers
from app.utils.urls import is_valid_telegram_button_url

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
# Se silencian loggers que podrían volcar datos sensibles o ruido innecesario
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Ciclo de vida: crea las tablas, inicia el bot y libera recursos."""
    # Creación automática de tablas (ver README: decisión y limitaciones)
    Base.metadata.create_all(bind=engine)
    logger.info("Esquema de base de datos verificado")

    if not is_valid_telegram_button_url(settings.frontend_url):
        logger.warning(
            "FRONTEND_URL=%s no es válida para botones inline de Telegram "
            "(p. ej. localhost): los enlaces al panel se enviarán como texto. "
            "Use una URL pública para mostrar botones.",
            settings.frontend_url,
        )

    bot_application = None
    if settings.telegram_bot_token:
        try:
            bot_application = build_application(settings.telegram_bot_token)
            await start_bot(bot_application)
            bot_state.set_status("running")
            logger.info("Bot de Telegram iniciado en modo polling")
        except Exception:  # noqa: BLE001
            # Un fallo del bot no debe impedir que la API funcione
            logger.exception("No fue posible iniciar el bot de Telegram")
            bot_state.set_status("error")
            bot_application = None
    else:
        bot_state.set_status("disabled")
        logger.warning("TELEGRAM_BOT_TOKEN vacío: el bot queda deshabilitado")

    try:
        yield
    finally:
        if bot_application is not None:
            try:
                await stop_bot(bot_application)
                logger.info("Bot de Telegram detenido")
            except Exception:  # noqa: BLE001
                logger.exception("Error al detener el bot de Telegram")
            bot_state.set_status("disabled")
        engine.dispose()


app = FastAPI(
    title="API de Ubicación Compartida (MVP)",
    description=(
        "API REST para el sistema de compartición voluntaria de ubicación mediante "
        "un bot de Telegram. La autenticación web se realiza con un código de un "
        "solo uso generado desde el bot (`/web`), canjeado por un JWT cuya "
        "identidad es el `telegram_id` del usuario."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS restringido a los orígenes del frontend configurados
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(authorizations.router)
app.include_router(locations.router)
app.include_router(invitations.router)
app.include_router(config.router)
