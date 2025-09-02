#!/usr/bin/env python3
"""
빠른 데이터베이스 스키마 확인 및 수정 스크립트 (API를 통한 접근)
"""

import os
import requests
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def quick_schema_check():
    """빠른 스키마 확인 및 수정 (API를 통한 접근)"""
    print("🔍 빠른 스키마 확인 및 수정 (API를 통한 접근)")
    print("=" * 50)
    
    # API 서버 URL
    api_base_url = os.getenv('API_URL', 'http://localhost:8000')
    print(f"🌐 API 서버: {api_base_url}")
    
    try:
        # 1. API 서버 상태 확인
        print("\n📡 API 서버 상태 확인...")
        response = requests.get(f"{api_base_url}/health")
        if response.status_code != 200:
            print(f"❌ API 서버 연결 실패: {response.status_code}")
            return
        print("✅ API 서버 연결 성공")
        
        # 2. 비디오 목록 조회
        print("\n📋 비디오 목록 조회:")
        response = requests.get(f"{api_base_url}/videos")
        if response.status_code == 200:
            videos = response.json()
            if videos:
                for video in videos:
                    print(f"  - ID: {video.get('id')}, 드라마: {video.get('drama_name')}, 에피소드: {video.get('episode_number')}")
            else:
                print("  ℹ️ 등록된 비디오가 없습니다.")
        else:
            print(f"❌ 비디오 목록 조회 실패: {response.status_code}")
        
        # 3. 테스트 비디오 생성
        print("\n🧪 테스트 비디오 생성...")
        test_video = {
            "video_unique_id": 9998,
            "drama_name": "TEST",
            "episode_number": "TEST"
        }
        
        response = requests.post(f"{api_base_url}/videos", json=test_video)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 테스트 비디오 생성 성공: {result.get('message')}")
        else:
            print(f"❌ 테스트 비디오 생성 실패: {response.text}")
        
        print("\n✅ 스키마 확인 완료 (API를 통한 접근)")
        
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    quick_schema_check()
