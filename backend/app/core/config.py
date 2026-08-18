from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Seller Management SaaS"
    app_env: str = "development"
    app_debug: bool = True

    database_url: str = (
        "postgresql+psycopg://seller:seller_dev_password@postgres:5432/seller_management"
    )

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    frontend_url: str = "http://localhost:3000"

    trusted_proxies: list[str] = []

    redis_url: str = ""
    redis_enabled: bool = False

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Seller Manager <no-reply@sellermanager.app>"
    smtp_use_tls: bool = True
    email_enabled: bool = False

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
