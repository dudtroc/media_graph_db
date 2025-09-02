"""
환경 변수 설정 관리
"""

import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 데이터베이스 설정
    DB_HOST: str = "localhost"
    DB_NAME: str = "scene_graph_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_PORT: str = "5432"
    
    # API 서버 설정
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 전역 설정 인스턴스
_settings = None

def get_settings() -> Settings:
    """설정 인스턴스 반환 (싱글톤 패턴)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# 환경 변수에서 직접 가져오는 함수들 (기존 코드 호환성)
def get_db_config() -> dict:
    """데이터베이스 연결 설정 반환"""
    settings = get_settings()
    return {
        'host': settings.DB_HOST,
        'database': settings.DB_NAME,
        'user': settings.DB_USER,
        'password': settings.DB_PASSWORD,
        'port': settings.DB_PORT
    }

