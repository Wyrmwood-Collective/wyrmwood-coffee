import os
import subprocess
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from wyrmwood_coffee.database import Base, get_db
from wyrmwood_coffee.main import app
from wyrmwood_coffee.settings import settings


def create_test_database(db_url: str) -> None:
    url = make_url(cast(str, settings.test_database_url))

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    args = ["createdb"]
    if url.username:
        args.extend(["-U", url.username])
    if url.host:
        args.extend(["-h", url.host])
    if url.port:
        args.extend(["-p", str(url.port)])
    if url.database:
        args.append(url.database)

    subprocess.run(args, env=env, check=True)


def destroy_test_database(db_name: str) -> None:
    url = make_url(cast(str, settings.test_database_url))

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    args = ["dropdb"]
    if url.username:
        args.extend(["-U", url.username])
    if url.host:
        args.extend(["-h", url.host])
    if url.port:
        args.extend(["-p", str(url.port)])
    if url.database:
        args.append(url.database)

    subprocess.run(args, env=env, check=True)


@pytest.fixture(scope="session")
def db_engine(request):
    db_name = cast(str, settings.test_database_url).split("/")[-1]
    db_url = cast(str, settings.test_database_url)
    create_test_database(db_name)
    request.addfinalizer(lambda: destroy_test_database(db_name))

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    del app.dependency_overrides[get_db]
