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

    if _engine is not None:
        return _engine

    match settings.app_environment:
        case Environment.DEV:
            if not settings.dev_database_url:
                logger.critical(
                    "DEV_DATABASE_URL is not set. Please configure it before running."
                )
                sys.exit(1)

            logger.info("Connecting to development database")
            _engine = create_engine(settings.dev_database_url)

        case Environment.STAGING:
            if not settings.staging_database_url:
                logger.critical(
                    "STAGING_DATABASE_URL is not set."
                    "Please configure it before running."
                )
                sys.exit(1)

            logger.info("Connecting to staging database")
            _engine = create_engine(settings.staging_database_url)

        case Environment.TEST:
            if not settings.test_database_url:
                logger.critical(
                    "TEST_DATABASE_URL is not set. Please configure it before running."
                )
                sys.exit(1)

            logger.info("Connecting to test database")
            _engine = create_engine(settings.test_database_url)

        case _:
            raise RuntimeError(
                f"Unsupported application environment: {settings.app_environment}"
            )

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
