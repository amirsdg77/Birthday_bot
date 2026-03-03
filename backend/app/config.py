"""
Config — loads all environment variables from .env
Add new config values here as the project grows.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    TEMPERATURE: float = 0.8
    MAX_TOKENS: int = 1024
    # Password Orgese must enter to access the chatbot
    ACCESS_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()
