#!/usr/bin/env python3
"""
데이터베이스 스키마 테스트 및 수정 스크립트 (API를 통한 접근)
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class DatabaseSchemaTester:
    """데이터베이스 스키마 테스트 및 수정 클래스 (API를 통한 접근)"""
    
    def __init__(self):
        """초기화"""
        self.api_base_url = os.getenv('API_URL', 'http://localhost:8000')
        print(f"🌐 API 서버: {self.api_base_url}")
    
    def check_api_connection(self):
        """API 서버 연결 확인"""
        try:
            response = requests.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                print("✅ API 서버 연결 성공")
                return True
            else:
                print(f"❌ API 서버 연결 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API 서버 연결 실패: {e}")
            return False
    
    def get_all_videos(self):
        """모든 비디오 목록 조회"""
        print("\n📋 데이터베이스의 모든 비디오:")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.api_base_url}/videos")
            if response.status_code == 200:
                videos = response.json()
                if videos:
                    for video in videos:
                        print(f"  - ID: {video.get('id')}, 드라마: {video.get('drama_name')}, 에피소드: {video.get('episode_number')}")
                else:
                    print("  ℹ️ 등록된 비디오가 없습니다.")
                return videos
            else:
                print(f"❌ 비디오 목록 조회 실패: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 비디오 목록 조회 오류: {e}")
            return []
    
    def test_video_creation(self):
        """비디오 생성 테스트"""
        print("\n🧪 비디오 생성 테스트:")
        print("-" * 40)
        
        test_video = {
            "video_unique_id": 9999,
            "drama_name": "TEST_DRAMA",
            "episode_number": "TEST_EP"
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/videos", json=test_video)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 테스트 비디오 생성 성공: {result.get('message')}")
                return result.get('video_id')
            else:
                print(f"❌ 테스트 비디오 생성 실패: {response.text}")
                return None
        except Exception as e:
            print(f"❌ 테스트 비디오 생성 오류: {e}")
            return None
    
    def test_scene_creation(self, video_unique_id: int):
        """장면 생성 테스트"""
        print(f"\n🎭 장면 생성 테스트 (Video ID: {video_unique_id}):")
        print("-" * 40)
        
        test_scene = {
            "video_unique_id": video_unique_id,
            "scene_data": {
                "scene_number": "TEST_SCENE",
                "scene_place": "테스트 장소",
                "scene_time": "테스트 시간",
                "scene_atmosphere": "테스트 분위기"
            },
            "pt_data": {
                "z": [[0.1, 0.2, 0.3]],  # 간단한 임베딩 벡터
                "orig_id": ["test_node_1"]
            }
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/scenes", json=test_scene)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 테스트 장면 생성 성공: {result.get('message')}")
                return result.get('scene_id')
            else:
                print(f"❌ 테스트 장면 생성 실패: {response.text}")
                return None
        except Exception as e:
            print(f"❌ 테스트 장면 생성 오류: {e}")
            return None
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🔍 데이터베이스 스키마 테스트 시작 (API를 통한 접근)")
        print("=" * 60)
        
        # 1. API 연결 확인
        if not self.check_api_connection():
            print("❌ API 서버에 연결할 수 없어 테스트를 중단합니다.")
            return
        
        # 2. 기존 비디오 목록 확인
        existing_videos = self.get_all_videos()
        
        # 3. 테스트 비디오 생성
        test_video_id = self.test_video_creation()
        
        # 4. 테스트 장면 생성
        if test_video_id:
            test_scene_id = self.test_scene_creation(test_video_id)
            if test_scene_id:
                print(f"\n✅ 모든 테스트 완료!")
                print(f"  - 생성된 비디오 ID: {test_video_id}")
                print(f"  - 생성된 장면 ID: {test_scene_id}")
            else:
                print("\n❌ 장면 생성 테스트 실패")
        else:
            print("\n❌ 비디오 생성 테스트 실패")
        
        print("\n📝 참고: 이 스크립트는 API를 통해서만 데이터베이스에 접근합니다.")
        print("   직접적인 데이터베이스 연결은 보안상 허용되지 않습니다.")

def main():
    """메인 함수"""
    tester = DatabaseSchemaTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
