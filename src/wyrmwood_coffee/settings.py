"""Load app settings from the environment, not from hard-coded secrets.

On a laptop, values usually come from `.env.local` (see `.env.example`).
In CI or on a deployed host, the same names are set as environment variables.
Missing or placeholder secrets stop the process with a clear error.
"""

import logging
from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, ValidationError, model_validator
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


class Settings(BaseSettings):
    app_environment: Environment = Environment.DEV
    dev_database_url: Annotated[str | None, Sensitive] = None
    test_database_url: Annotated[str | None, Sensitive] = None
    staging_database_url: Annotated[str | None, Sensitive] = None
    jwt_secret_key: Annotated[str, Sensitive] = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = Field(default=30, gt=0)
    log_level: LogLevel = LogLevel.WARNING

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    @model_validator(mode="after")
    def validate_required_secrets(self) -> Self:
        match self.app_environment:
            case Environment.TEST:
                _require_database_url(
                    self.test_database_url,
                    setting_name="TEST_DATABASE_URL",
                    environment="test",
                    local_hint=True,
                )
            case Environment.STAGING:
                _require_database_url(
                    self.staging_database_url,
                    setting_name="STAGING_DATABASE_URL",
                    environment="staging",
                    local_hint=False,
                )
            case Environment.DEV:
                _require_database_url(
                    self.dev_database_url,
                    setting_name="DEV_DATABASE_URL",
                    environment="dev",
                    local_hint=True,
                )

        if self.jwt_secret_key in PLACEHOLDER_JWT_SECRETS:
            raise ValueError(
                "JWT_SECRET_KEY is still the example placeholder. "
                "Generate a unique random string of at least 32 characters."
            )
        if (
            self.app_environment != Environment.TEST
            and self.jwt_secret_key in TEST_ONLY_JWT_SECRETS
        ):
            raise ValueError(
                "JWT_SECRET_KEY is the CI test value and cannot be used when "
                f"APP_ENVIRONMENT={self.app_environment}."
            )
        return self

    @property
    def database_url(self) -> str:
        match self.app_environment:
            case Environment.TEST:
                assert self.test_database_url is not None
                return self.test_database_url
            case Environment.STAGING:
                assert self.staging_database_url is not None
                return self.staging_database_url
            case Environment.DEV:
                assert self.dev_database_url is not None
                return self.dev_database_url


def _require_database_url(
    url: str | None,
    *,
    setting_name: str,
    environment: str,
    local_hint: bool,
) -> None:
    if not url:
        where = (
            "Set it in .env.local (local) or the process environment."
            if local_hint
            else "Set it as an environment variable on the deployed host."
        )
        raise ValueError(
            f"{setting_name} is required when APP_ENVIRONMENT={environment}. {where}"
        )
    if _contains_placeholder_database_url(url):
        raise ValueError(
            f"{setting_name} still uses a placeholder value. "
            "Replace USER:PASSWORD (and HOST for staging) with real credentials."
        )


def _contains_placeholder_database_url(url: str) -> bool:
    return any(marker in url for marker in PLACEHOLDER_DATABASE_MARKERS)


def _format_settings_error(exc: ValidationError) -> str:
    lines = [
        "Application cannot start: required configuration is missing or invalid.",
        "",
    ]
    for err in exc.errors():
        loc = err.get("loc", ())
        name = ""
        if loc:
            field = loc[0]
            if isinstance(field, str) and field in Settings.model_fields:
                name = f"{field.upper()}: "
        lines.append(f"  - {name}{err['msg']}")
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


def load_settings(**kwargs) -> Settings:
    try:
        return Settings(**kwargs)  # type: ignore[call-arg]
    except ValidationError as exc:
        logger.critical(_format_settings_error(exc))
        raise SystemExit(1) from exc


settings = load_settings()
