import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from wyrmwood_coffee.settings import settings

logger = logging.getLogger(__name__)

_engine = None


def get_engine() -> Engine:
    global _engine

    if _engine is not None:
        return _engine

    logger.info("Connecting to %s database", settings.app_environment)
    _engine = create_engine(settings.database_url)
    return _engine


_SessionLocal = None


def get_session_local() -> sessionmaker[Session]:
    global _SessionLocal

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
        return _SessionLocal
    else:
        return _SessionLocal


Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
