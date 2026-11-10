"""Servicio de configuración de privacidad del usuario."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserConfig
from app.utils.dates import utcnow


def get(db: Session, user_id: int) -> UserConfig:
    """Devuelve la configuración del usuario, creándola con valores por defecto."""
    config = db.scalar(select(UserConfig).where(UserConfig.usuario_id == user_id))
    if config is None:
        config = UserConfig(
            usuario_id=user_id,
            compartir_ubicacion=False,
            fecha_actualizacion=utcnow(),
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def set_sharing(db: Session, user_id: int, compartir: bool) -> UserConfig:
    """Activa o detiene la compartición de ubicación (consentimiento explícito)."""
    config = get(db, user_id)
    config.compartir_ubicacion = compartir
    config.fecha_actualizacion = utcnow()
    db.commit()
    return config


def owners_sharing(db: Session, user_ids: list[int]) -> set[int]:
    """Devuelve el subconjunto de usuarios que tienen la compartición activada."""
    if not user_ids:
        return set()
    stmt = select(UserConfig.usuario_id).where(
        UserConfig.usuario_id.in_(user_ids),
        UserConfig.compartir_ubicacion.is_(True),
    )
    return set(db.scalars(stmt).all())
