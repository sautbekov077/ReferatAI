from pydantic_settings import BaseSettings

CORS_ALLOW_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()
]

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = "tngtech/deepseek-r1t-chimera:free"
    TIMEOUT: int = 180

    class Config:
        env_file = ".env"

settings = Settings()

