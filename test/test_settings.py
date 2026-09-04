"""Settings loading, fail-fast behavior, and secrets-policy checks."""

import logging
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from wyrmwood_coffee.logging import Sensitive
from wyrmwood_coffee.settings import Settings, load_settings

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"

REQUIRED_EXAMPLE_VARS = {
    "APP_ENVIRONMENT",
    "DEV_DATABASE_URL",
    "TEST_DATABASE_URL",
    "STAGING_DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "JWT_EXPIRATION_MINUTES",
}

VALID_DEV_DATABASE_URL = (
    "postgresql+psycopg://localuser:localpass@localhost:5432/wyrmwood_coffee"
)
VALID_TEST_DATABASE_URL = (
    "postgresql+psycopg://localuser:localpass@localhost:5432/wyrmwood_coffee_test"
)
VALID_STAGING_DATABASE_URL = (
    "postgresql+psycopg://staginguser:stagingpass@db.example.com:5432/wyrmwood_coffee"
)
VALID_JWT_SECRET_KEY = "local-dev-jwt-secret-key-not-a-real-secret"

SETTINGS_LOGGER = "wyrmwood_coffee.settings"


def _example_env_keys():
    keys = set()
    for line in ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0])
    return keys


def _clear_settings_env(monkeypatch):
    for key in REQUIRED_EXAMPLE_VARS:
        monkeypatch.delenv(key, raising=False)


def test_load_settings_with_valid_env_should_succeed(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    loaded = load_settings(_env_file=None)

    assert loaded.app_environment == "dev"
    assert loaded.database_url == VALID_DEV_DATABASE_URL
    assert loaded.jwt_secret_key == VALID_JWT_SECRET_KEY


def test_load_settings_with_valid_test_env_should_succeed(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("TEST_DATABASE_URL", VALID_TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-not-for-production")

    loaded = load_settings(_env_file=None)

    assert loaded.app_environment == "test"
    assert loaded.database_url == VALID_TEST_DATABASE_URL


def test_load_settings_with_valid_staging_env_should_succeed(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("STAGING_DATABASE_URL", VALID_STAGING_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    loaded = load_settings(_env_file=None)

    assert loaded.app_environment == "staging"
    assert loaded.database_url == VALID_STAGING_DATABASE_URL


def test_load_settings_with_missing_jwt_secret_key_should_exit(monkeypatch, caplog):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "Application cannot start" in caplog.text
    assert "JWT_SECRET_KEY" in caplog.text


def test_load_settings_with_missing_dev_database_url_should_exit(monkeypatch, caplog):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "DEV_DATABASE_URL" in caplog.text


def test_load_settings_with_missing_test_database_url_should_exit(monkeypatch, caplog):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "TEST_DATABASE_URL" in caplog.text


def test_load_settings_with_missing_staging_database_url_should_exit(
    monkeypatch, caplog
):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "STAGING_DATABASE_URL" in caplog.text


def test_load_settings_with_placeholder_jwt_secret_key_should_exit(monkeypatch, caplog):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", "change-me-must-be-at-least-32-characters")

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "placeholder" in caplog.text.lower()


def test_load_settings_with_placeholder_database_url_should_exit(monkeypatch, caplog):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv(
        "DEV_DATABASE_URL",
        "postgresql+psycopg://USER:PASSWORD@localhost:5432/wyrmwood_coffee",
    )
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "DEV_DATABASE_URL" in caplog.text
    assert "placeholder" in caplog.text.lower()


def test_load_settings_with_placeholder_test_database_url_should_exit(
    monkeypatch, caplog
):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://USER:PASSWORD@localhost:5432/wyrmwood_coffee_test",
    )
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "TEST_DATABASE_URL" in caplog.text
    assert "placeholder" in caplog.text.lower()


def test_load_settings_with_placeholder_staging_database_url_should_exit(
    monkeypatch, caplog
):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv(
        "STAGING_DATABASE_URL",
        "postgresql+psycopg://USER:PASSWORD@HOST:5432/wyrmwood_coffee",
    )
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "STAGING_DATABASE_URL" in caplog.text
    assert "placeholder" in caplog.text.lower()


def test_load_settings_with_ci_jwt_in_dev_should_exit(monkeypatch, caplog):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-not-for-production")

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "CI test value" in caplog.text


def test_load_settings_with_ci_jwt_in_staging_should_exit(monkeypatch, caplog):
    caplog.set_level(logging.CRITICAL, logger=SETTINGS_LOGGER)
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("STAGING_DATABASE_URL", VALID_STAGING_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-not-for-production")

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert exc_info.value.code == 1
    assert "CI test value" in caplog.text


def test_settings_jwt_secret_key_has_no_default():
    assert Settings.model_fields["jwt_secret_key"].is_required()


def test_settings_short_jwt_secret_key_should_raise(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short-to-be-valid")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "jwt_secret_key" in str(exc_info.value)


def test_env_example_should_document_every_required_variable():
    keys = _example_env_keys()
    missing = REQUIRED_EXAMPLE_VARS - keys
    assert not missing, f".env.example is missing {sorted(missing)}"


def test_env_example_should_not_contain_real_secret_values():
    contents = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "USER:PASSWORD" in contents
    assert "@HOST:" in contents
    assert "change-me-must-be-at-least-32-characters" in contents
    assert "root:root" not in contents


def test_secret_env_files_should_not_be_tracked():
    tracked = (
        subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
        )
        .decode()
        .split("\0")
    )
    forbidden = {".env", ".env.local"}
    leaked = forbidden.intersection(tracked)
    assert not leaked, f"Secret env files are tracked: {sorted(leaked)}"


def test_env_local_should_be_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".env.local"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_env_example_should_not_be_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".env.example"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 1


def test_gitignore_should_keep_env_example_unignored():
    contents = GITIGNORE_PATH.read_text(encoding="utf-8")
    assert ".env" in contents
    assert "!.env.example" in contents


def test_settings_secret_fields_are_marked_sensitive():
    from wyrmwood_coffee.logging import sensitive_field_names
    from wyrmwood_coffee.settings import Settings

    for field_name in (
        "jwt_secret_key",
        "dev_database_url",
        "test_database_url",
        "staging_database_url",
    ):
        field = Settings.model_fields[field_name]
        assert Sensitive in field.metadata, f"{field_name} missing Sensitive marker"

    names = sensitive_field_names()
    assert {
        "jwt_secret_key",
        "dev_database_url",
        "test_database_url",
        "staging_database_url",
    }.issubset(names)
