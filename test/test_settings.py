"""Settings loading, validation, and secrets-policy checks."""

import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from wyrmwood_coffee.logging import Sensitive, sensitive_field_names
from wyrmwood_coffee.settings import (
    AuthSettings,
    CoreSettings,
    DatabaseSettings,
    Environment,
    LogLevel,
    _load_app_settings,
    _load_script_settings,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"

REQUIRED_EXAMPLE_VARS = {
    "DEV_DATABASE_URL",
    "TEST_DATABASE_URL",
    "JWT_SECRET_KEY",
}

ENV_VARS_UNDER_TEST = {
    "APP_ENVIRONMENT",
    "DEV_DATABASE_URL",
    "TEST_DATABASE_URL",
    "STAGING_DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "JWT_EXPIRATION_MINUTES",
    "LOG_LEVEL",
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
CI_ONLY_JWT_SECRET_KEY = "test-jwt-secret-key-not-for-production"


def _example_env_keys():
    keys = set()
    for line in ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0])
    return keys


def _clear_settings_env(monkeypatch):
    for key in ENV_VARS_UNDER_TEST:
        monkeypatch.delenv(key, raising=False)


def test_load_app_settings_with_valid_dev_env_should_succeed(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    loaded = _load_app_settings()

    assert loaded.core.app_environment == Environment.DEV
    assert loaded.database.url == VALID_DEV_DATABASE_URL
    assert loaded.auth.jwt_secret_key == VALID_JWT_SECRET_KEY


def test_load_app_settings_with_valid_test_env_should_succeed(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("TEST_DATABASE_URL", VALID_TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    loaded = _load_app_settings()

    assert loaded.core.app_environment == Environment.TEST
    assert loaded.database.url == VALID_TEST_DATABASE_URL


def test_load_app_settings_with_valid_staging_env_should_succeed(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("STAGING_DATABASE_URL", VALID_STAGING_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_JWT_SECRET_KEY)

    loaded = _load_app_settings()

    assert loaded.core.app_environment == Environment.STAGING
    assert loaded.database.url == VALID_STAGING_DATABASE_URL


def test_load_script_settings_uses_environment_specific_database_prefix(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("STAGING_DATABASE_URL", VALID_STAGING_DATABASE_URL)
    # A DEV_DATABASE_URL set alongside it should be ignored for staging.
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)

    script = _load_script_settings()

    assert script.core.app_environment == Environment.STAGING
    assert script.database.url == VALID_STAGING_DATABASE_URL


def test_auth_settings_with_missing_jwt_secret_key_should_raise(monkeypatch):
    # _env_file=None bypasses .env/.env.local so a developer's local secret
    # can't mask the "missing" case.
    _clear_settings_env(monkeypatch)

    with pytest.raises(ValidationError) as exc_info:
        AuthSettings(_env_file=None)  # type: ignore[call-arg]

    assert "jwt_secret_key" in str(exc_info.value)


def test_database_settings_with_missing_url_should_raise(monkeypatch):
    _clear_settings_env(monkeypatch)

    with pytest.raises(ValidationError) as exc_info:
        DatabaseSettings(_env_prefix="DEV_DATABASE_", _env_file=None)  # type: ignore[call-arg]

    assert "url" in str(exc_info.value)


def test_load_app_settings_with_placeholder_jwt_secret_key_should_raise(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", "change-me-must-be-at-least-32-characters")

    with pytest.raises(ValidationError) as exc_info:
        _load_app_settings()

    assert "placeholder" in str(exc_info.value).lower()


def test_load_app_settings_with_ci_jwt_in_dev_should_raise(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "dev")
    monkeypatch.setenv("DEV_DATABASE_URL", VALID_DEV_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", CI_ONLY_JWT_SECRET_KEY)

    with pytest.raises(ValidationError) as exc_info:
        _load_app_settings()

    assert "CI test value" in str(exc_info.value)


def test_load_app_settings_with_ci_jwt_in_staging_should_raise(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("STAGING_DATABASE_URL", VALID_STAGING_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", CI_ONLY_JWT_SECRET_KEY)

    with pytest.raises(ValidationError) as exc_info:
        _load_app_settings()

    assert "CI test value" in str(exc_info.value)


def test_load_app_settings_with_ci_jwt_in_test_should_succeed(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("TEST_DATABASE_URL", VALID_TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", CI_ONLY_JWT_SECRET_KEY)

    loaded = _load_app_settings()

    assert loaded.auth.jwt_secret_key == CI_ONLY_JWT_SECRET_KEY


def test_settings_jwt_secret_key_has_no_default():
    assert AuthSettings.model_fields["jwt_secret_key"].is_required()


def test_settings_short_jwt_secret_key_should_raise(monkeypatch):
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short-to-be-valid")

    with pytest.raises(ValidationError) as exc_info:
        AuthSettings()  # type: ignore[call-arg]

    assert "jwt_secret_key" in str(exc_info.value)


def test_core_settings_defaults_to_dev_and_warning(monkeypatch):
    _clear_settings_env(monkeypatch)

    core = CoreSettings(_env_file=None)  # type: ignore[call-arg]

    assert core.app_environment == Environment.DEV
    assert core.log_level == LogLevel.WARNING


def test_env_example_should_document_every_required_variable():
    keys = _example_env_keys()
    missing = REQUIRED_EXAMPLE_VARS - keys
    assert not missing, f".env.example is missing {sorted(missing)}"


def test_env_example_should_not_contain_real_secret_values():
    contents = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "USER:PASSWORD" in contents
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
    assert Sensitive in AuthSettings.model_fields["jwt_secret_key"].metadata
    assert Sensitive in DatabaseSettings.model_fields["url"].metadata

    names = sensitive_field_names()
    assert {"jwt_secret_key", "url"}.issubset(names)
