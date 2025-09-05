#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
SQLAlchemy ORM을 사용하여 데이터베이스 테이블을 생성합니다.
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.orm_models import create_tables, engine
from database.database_manager import SceneGraphDatabaseManager

def main():
    """데이터베이스 초기화 메인 함수"""
    print("🚀 데이터베이스 초기화 시작")
    print("=" * 50)
    
    try:
        # 1. 테이블 생성
        print("📋 SQLAlchemy ORM 테이블 생성 중...")
        create_tables()
        print("✅ 테이블 생성 완료")
        
        # 2. 데이터베이스 매니저 테스트
        print("\n🔗 데이터베이스 연결 테스트 중...")
        db_manager = SceneGraphDatabaseManager()
        print("✅ 데이터베이스 매니저 초기화 완료")
        
        # 3. 간단한 테스트 데이터 삽입
        print("\n🧪 테스트 데이터 삽입 중...")
        video_id = db_manager.insert_video_data(
            video_unique_id=9999,
            drama_name="테스트 드라마",
            episode_number="EP01"
        )
        print(f"✅ 테스트 비디오 생성 완료 (ID: {video_id})")
        
        # 4. 테스트 데이터 조회
        print("\n📊 테스트 데이터 조회 중...")
        videos = db_manager.get_all_videos()
        print(f"✅ 총 {len(videos)}개의 비디오가 있습니다")
        
        # 5. 연결 종료
        db_manager.close()
        print("\n✅ 데이터베이스 초기화 완료!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
