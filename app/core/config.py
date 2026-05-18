from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    telegram_bot_token: str

    class Config:
        env_file = ".env"

settings = Settings()