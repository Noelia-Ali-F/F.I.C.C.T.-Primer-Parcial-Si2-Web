from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FICCT Diagramador API"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api"

    postgres_db: str = "diagramador"
    postgres_user: str = "diagramador"
    postgres_password: str = "diagramador"
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_connect_timeout: int = 5
    uploads_dir: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
