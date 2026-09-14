"""Load app settings from the environment, not from hard-coded secrets.

On a laptop, values usually come from `.env.local` (see `.env.example`).
In CI or on a deployed host, the same names are set as environment variables.
Missing or placeholder secrets stop the process with a clear error.
"""

import logging
import os
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from wyrmwood_coffee.logging import Sensitive

logger = logging.getLogger(__name__)

PLACEHOLDER_JWT_SECRETS = frozenset(
    {
        "change-me-must-be-at-least-32-characters",
        "replace-me-with-a-long-random-string",
    }
)

TEST_ONLY_JWT_SECRETS = frozenset(
    {
        "test-jwt-secret-key-not-for-production",
    }
)

PLACEHOLDER_DATABASE_MARKERS = (
    "://USER:PASSWORD@",
    "://username:password@",
    "@HOST:",
)


class Environment(StrEnum):
    DEV = "dev"
    TEST = "test"
    STAGING = "staging"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )


class CoreSettings(BaseAppSettings):
    app_environment: Environment = Environment.DEV
    log_level: LogLevel = LogLevel.WARNING


class DatabaseSettings(BaseAppSettings):
    url: Annotated[str, Sensitive]

    @model_validator(mode="after")
    def validate_url(self) -> Self:
        if _contains_placeholder_database_url(self.url):
            raise ValueError(
                "DATABASE_URL still uses a placeholder value. "
                "Replace USER:PASSWORD (and HOST) with real credentials."
            )
        return self


def _contains_placeholder_database_url(url: str) -> bool:
    return any(marker in url for marker in PLACEHOLDER_DATABASE_MARKERS)


def _load_database_settings(core: CoreSettings) -> DatabaseSettings:
    prefix = core.app_environment.upper()
    database = DatabaseSettings(_env_prefix=f"{prefix}_DATABASE_")  # type: ignore[call-arg]
    return database


class AuthSettings(BaseAppSettings):
    jwt_secret_key: Annotated[str, Sensitive] = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = Field(default=30, gt=0)

    @model_validator(mode="after")
    def validate_required_secrets(self) -> Self:
        if self.jwt_secret_key in PLACEHOLDER_JWT_SECRETS:
            raise ValueError(
                "JWT_SECRET_KEY is still the example placeholder. "
                "Generate a unique random string of at least 32 characters."
            )
        return self


class ScriptSettings(BaseModel):
    core: CoreSettings
    database: DatabaseSettings


def _load_script_settings() -> ScriptSettings:
    core = CoreSettings()
    database = _load_database_settings(core)
    return ScriptSettings(core=core, database=database)


_script_settings = None


def script_settings():
    global _script_settings
    if _script_settings:
        return _script_settings

    _script_settings = _load_script_settings()
    return _script_settings


class AppSettings(ScriptSettings):
    auth: AuthSettings

    @model_validator(mode="after")
    def validate_required_secrets(self) -> Self:
        if (
            self.core.app_environment != Environment.TEST
            and self.auth.jwt_secret_key in TEST_ONLY_JWT_SECRETS
        ):
            raise ValueError(
                "JWT_SECRET_KEY is the CI test value and cannot be used when "
                f"APP_ENVIRONMENT={self.core.app_environment}."
            )
        return self


def _load_app_settings() -> AppSettings:
    script = _load_script_settings()
    auth = AuthSettings()  # type: ignore[call-arg]
    return AppSettings(core=script.core, database=script.database, auth=auth)


_app_settings = None


def app_settings():
    global _app_settings
    if _app_settings:
        return _app_settings

    _app_settings = _load_app_settings()
    return _app_settings


def _field_env_var_name(field: str) -> str:
    if field == "url":
        prefix = os.environ.get("APP_ENVIRONMENT", Environment.DEV.value).upper()
        return f"{prefix}_DATABASE_URL"
    return field.upper()


def _format_settings_error(exc: ValidationError) -> str:
    database_prefix = os.environ.get("APP_ENVIRONMENT", Environment.DEV.value).upper()
    lines = [
        "Application cannot start: required configuration is missing or invalid.",
        "",
    ]
    for err in exc.errors():
        loc = err.get("loc", ())
        name = ""
        msg = err["msg"]
        if loc and isinstance(loc[0], str):
            name = f"{_field_env_var_name(loc[0])}: "
        elif "DATABASE_URL" in msg:
            # Model-level validators (e.g. DatabaseSettings.validate_url) raise
            # a generic "DATABASE_URL" message with no field loc, since the
            # model itself doesn't know which environment's prefix applies.
            msg = msg.replace("DATABASE_URL", f"{database_prefix}_DATABASE_URL")
        lines.append(f"  - {name}{msg}")
    lines.extend(
        [
            "",
            "Local development: copy .env.example to .env.local and replace "
            "placeholders with real values. Never commit .env.local.",
            "Deployed staging: set APP_ENVIRONMENT=staging and "
            "STAGING_DATABASE_URL as environment variables on the host.",
            "See docs/configuration.md.",
        ]
    )
    return "\n".join(lines)


def require_app_settings() -> AppSettings:
    """Eagerly validate every required setting, stopping the process with a
    clear error if any are missing or invalid. Call this once at process
    startup (see main.py).

    Scripts that don't touch auth (`seed`, `alembic`) should call
    `script_settings()` instead, since they don't require `JWT_SECRET_KEY`.
    """
    try:
        return _load_app_settings()
    except ValidationError as exc:
        logger.critical(_format_settings_error(exc))
        raise SystemExit(1) from exc
