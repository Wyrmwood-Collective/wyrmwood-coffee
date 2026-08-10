import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from wyrmwood_coffee.settings import settings

if settings.database_url is None:
    sys.exit("Error: DATABASE_URL is not set. Please configure it before running.")

engine = create_engine(settings.database_url)

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
