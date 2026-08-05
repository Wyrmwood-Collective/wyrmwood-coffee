from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    pg_dsn: PostgresDsn = PostgresDsn("postgres://localhost/wyrmwood_coffee_dev")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
