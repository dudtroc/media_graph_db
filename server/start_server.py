#!/usr/bin/env python3
"""
Scene Graph Database API 서버 실행 스크립트
"""

import uvicorn
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

if __name__ == "__main__":
    print("🚀 Scene Graph Database API 서버 시작")
    print("=" * 50)
    
    # 서버 설정
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("API_DEBUG", "True").lower() == "true"
    
    print(f"📍 서버 주소: http://{host}:{port}")
    print(f"🔧 디버그 모드: {debug}")
    print(f"🗄️  데이터베이스: {os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}")
    print("=" * 50)
    
    # 서버 실행
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
