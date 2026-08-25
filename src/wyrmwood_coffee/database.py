import logging
import sys
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from wyrmwood_coffee.settings import Environment, settings

logger = logging.getLogger(__name__)

_engine = None


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        match settings.app_environment:
            case Environment.DEV:
                if settings.dev_database_url:
                    logger.info("Connecting to development database")
                    _engine = create_engine(settings.dev_database_url)
                    return _engine
                else:
                    logger.critical(
                        "DATABASE_URL is not set. Please configure it before running."
                    )
                    sys.exit(1)
            case Environment.TEST:
                if settings.test_database_url:
                    logger.info("Connecting to test database")
                    _engine = create_engine(settings.test_database_url)
                    return _engine
                else:
                    logger.critical(
                        "TEST_DATABASE_URL is not set. Please configure it before running."  # noqa: E501
                    )
                    sys.exit(1)
    else:
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
