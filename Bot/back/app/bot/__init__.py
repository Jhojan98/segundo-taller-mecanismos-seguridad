"""Paquete del bot de Telegram.

El bot se ejecuta dentro del mismo proceso que FastAPI: se inicializa en el
ciclo de vida (`lifespan`) de la aplicación y usa polling, por lo que no
requiere dominio público ni configuración de webhook.
"""
