#!/usr/bin/env python3
"""
Scene Graph Database API 서버 시작 스크립트
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """서버 시작"""
    print("🚀 Scene Graph Database API 서버 시작")
    print("=" * 50)
    
    # Check database connection only (no initialization)
    print("🔧 Checking database connection...")
    try:
        from database.database_manager import SceneGraphDatabaseManager
        db_manager = SceneGraphDatabaseManager()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("💡 Please run 'python init_database.py' first to initialize the database")
        print("💡 Continuing with server start...")
    
    # 서버 설정
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("API_DEBUG", "True").lower() == "true"
    
    print(f"🌐 서버 주소: http://{host}:{port}")
    print(f"🔧 디버그 모드: {debug}")
    print(f"📚 API 문서: http://{host}:{port}/docs")
    print("=" * 50)
    
    # 서버 시작
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )

if __name__ == "__main__":
    main()
