"""Guardrails around seeding the staging environment."""

import logging
from types import SimpleNamespace

import pytest

from wyrmwood_coffee.seed import _ensure_staging_seed_allowed
from wyrmwood_coffee.settings import Environment

SEED_LOGGER = "wyrmwood_coffee.seed"


@pytest.fixture
def staging_script_settings(monkeypatch):
    monkeypatch.setattr(
        "wyrmwood_coffee.seed.script_settings",
        lambda: SimpleNamespace(
            core=SimpleNamespace(app_environment=Environment.STAGING)
        ),
    )


def test_seed_staging_without_confirm_flag_should_exit(
    staging_script_settings, monkeypatch, caplog
):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    caplog.set_level(logging.CRITICAL, logger=SEED_LOGGER)

    with pytest.raises(SystemExit) as exc_info:
        _ensure_staging_seed_allowed(confirm_staging_seed=False)

    assert exc_info.value.code == 1
    assert "--confirm-staging-seed" in caplog.text


def test_seed_staging_with_confirm_flag_outside_github_actions_should_exit(
    staging_script_settings, monkeypatch, caplog
):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    caplog.set_level(logging.CRITICAL, logger=SEED_LOGGER)

    with pytest.raises(SystemExit) as exc_info:
        _ensure_staging_seed_allowed(confirm_staging_seed=True)

    assert exc_info.value.code == 1
    assert "GitHub Actions" in caplog.text


def test_seed_staging_with_confirm_flag_inside_github_actions_should_proceed(
    staging_script_settings, monkeypatch
):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    _ensure_staging_seed_allowed(confirm_staging_seed=True)


def test_seed_outside_staging_should_proceed_without_confirm_flag(monkeypatch):
    monkeypatch.setattr(
        "wyrmwood_coffee.seed.script_settings",
        lambda: SimpleNamespace(core=SimpleNamespace(app_environment=Environment.TEST)),
    )
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    _ensure_staging_seed_allowed(confirm_staging_seed=False)
