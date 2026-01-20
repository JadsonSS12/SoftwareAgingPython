from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Production REST API"
    environment: str = "production"
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
