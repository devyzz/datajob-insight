import os
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path # pathlib 추가

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOTENV_PATH = PROJECT_ROOT_DIR / ".env"

class CommonSettings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@host:port/db")
    API_SERVICE_BASE_URL: str = os.getenv("API_SERVICE_BASE_URL", "http://localhost:8000") 
    
    class Config:
        env_file = DOTENV_PATH # 프로젝트 루트의 .env 파일을 참조
        env_file_encoding = 'utf-8'
        extra = "ignore" # .env 파일에 없는 CommonSettings 필드는 무시

common_settings = CommonSettings()