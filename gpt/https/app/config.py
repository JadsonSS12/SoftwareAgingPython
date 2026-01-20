from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Production HTTP Server"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    class Config:
        env_file = ".env"


settings = Settings()
