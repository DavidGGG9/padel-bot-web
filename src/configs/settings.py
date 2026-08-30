from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Pydantic validates all fields at instantiation. If a required variable
    is missing, a ValidationError is raised immediately.

    """

    OUTPUT_PATH: str
    MDB_USER: str
    MDB_PASSWORD: SecretStr
    DB_NAME: str
    COLLECTION_NAME: str
    TIMEZONE: str

    model_config = SettingsConfigDict(
        env_file=".devcontainer/devcontainer.env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
    )

settings = Settings() # pyright ignore[reportCallIssue]