from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql://civicfix:civicfix@localhost:5432/civicfix"
    secret_key: str = "super-secret-key-change-in-production"
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    gemini_api_key: str = ""  # Get free key at https://aistudio.google.com

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
