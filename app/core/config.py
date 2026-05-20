from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    app_env: str = "development"
    cors_origin: str = "http://localhost:3000"
    telegram_bot_token: str

    class Config:
        env_file = ".env"

settings = Settings()