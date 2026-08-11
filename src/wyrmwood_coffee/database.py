
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from wyrmwood_coffee.settings import Environment, settings

match settings.app_environment:
    case Environment.DEV:
        if settings.dev_database_url:
            engine = create_engine(settings.dev_database_url)
        else:
            sys.exit(
                "Error: DATABASE_URL is not set. Please configure it before running."
            )
    case Environment.TEST:
        if settings.test_database_url:
            engine = create_engine(settings.test_database_url)
        else:
            sys.exit(
                "Error: TEST_DATABASE_URL is not set. Please configure it before running."  # noqa: E501
            )



SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
