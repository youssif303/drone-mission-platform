from pydantic_settings import BaseSettings
from typing import List


from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = 'Drone Mission Planning & Perception Platform'
    DATABASE_URL: str = 'sqlite+aiosqlite:///./drone_platform.db'
    DEMO_MODE: bool = True
    DEMO_DATA_DIR: str = str(BASE_DIR / 'simulation' / 'demo_data' / 'urban_patrol')
    CORS_ORIGINS: List[str] = ['http://localhost:5173', 'http://localhost:3000']
    WS_FRAME_RATE: int = 15

    class Config:
        env_file = ".env"

settings = Settings()
