import logging
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import wyrmwood_coffee.models as models_package
from wyrmwood_coffee.logging import (
    REDACTED,
    RequestContextFilter,
    redact_dict,
    request_context,
)
from wyrmwood_coffee.main import app


def test_request_context_filter_does_not_overwrite_existing_fields(caplog):
    caplog.set_level(logging.DEBUG, logger="wyrmwood_coffee.test_filter")
    filter_logger = logging.getLogger("wyrmwood_coffee.test_filter")
    context_filter = RequestContextFilter()
    filter_logger.addFilter(context_filter)

    token = request_context.set({"path": "/generic", "method": "GET"})
    try:
        filter_logger.debug("specific event", extra={"path": "/specific"})
    finally:
        request_context.reset(token)
        filter_logger.removeFilter(context_filter)

    record = caplog.records[-1]
    assert record.path == "/specific"
    assert record.method == "GET"


@pytest.fixture
def raising_route():
    """Register a throwaway route that always raises."""

    @app.get("/__raise")
    def _raise():
        raise RuntimeError("failure")

    yield "/__raise"

    app.router.routes = [
        route
        for route in app.router.routes
        if getattr(route, "path", None) != "/__raise"
    ]


def test_unhandled_exception_logs_error(caplog, raising_route):
    caplog.set_level(logging.ERROR, logger="wyrmwood_coffee.main")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(raising_route)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}

    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1

    error = errors[0]
    assert error.exc_info is not None
    assert error.exc_info[0] is RuntimeError
    assert error.method == "GET"
    assert error.path == raising_route


def test_password_is_redacted_in_request_log(client, caplog):
    caplog.set_level(logging.DEBUG, logger="wyrmwood_coffee.middleware")

    response = client.post(
        "/employees",
        json={
            "active": True,
            "first_name": "Ada",
            "last_name": "Lovelace",
            "role": "employee",
            "hourly_rate": 18.5,
            "hire_date": "2024-01-15",
            "username": "alovelace",
            "password": "Sup3r$ecret!",
        },
    )
    assert response.status_code == 201

    debug_records = [
        r for r in caplog.records if r.name == "wyrmwood_coffee.middleware"
    ]
    assert len(debug_records) == 1

    payload = debug_records[0].payload
    assert payload["password"] == REDACTED
    assert payload["username"] == "alovelace"


def test_redact_dict_redacts_nested_fields():
    data = {
        "name": "Ada",
        "credentials": {"password": "secret", "username": "ada"},
        "accounts": [{"password": "secret2"}, {"password": "secret3"}],
    }

    result = redact_dict(data, sensitive_names={"password"})

    assert result == {
        "name": "Ada",
        "credentials": {"password": REDACTED, "username": "ada"},
        "accounts": [{"password": REDACTED}, {"password": REDACTED}],
    }


def test_models_init_imports_every_model_module():
    """`sensitive_field_names()` only sees models that have been imported.

    `wyrmwood_coffee.models` is what guarantees every model gets imported,
    regardless of which routers happen to be loaded -- so if a new model
    file is added without also adding it here, redaction can silently miss
    a `Sensitive`-marked field. This test fails if that ever happens.
    """
    models_dir = Path(models_package.__file__).parent
    expected = sorted(
        path.stem for path in models_dir.glob("*.py") if path.stem != "__init__"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, wyrmwood_coffee.models\n"
            "print('\\n'.join(m for m in sys.modules "
            "if m.startswith('wyrmwood_coffee.models.')))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    imported = {line.rsplit(".", 1)[-1] for line in result.stdout.splitlines()}

    missing = set(expected) - imported
    assert not missing, f"models/__init__.py does not import: {sorted(missing)}"
