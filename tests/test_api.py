#!/usr/bin/env python3
"""
API 서버 테스트 클라이언트
"""

import requests
import json
import numpy as np

# API 서버 기본 URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """헬스 체크 테스트"""
    print("🔍 헬스 체크 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def test_create_video():
    """비디오 생성 테스트"""
    print("\n🎬 비디오 생성 테스트...")
    video_data = {
        "video_unique_id": 1001,
        "drama_name": "Kingdom",
        "episode_number": "EP01"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/videos", json=video_data)
        print(f"상태 코드: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 비디오 생성 성공: {result}")
            return result.get('video_id')
        else:
            print(f"❌ 비디오 생성 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None

def test_list_videos():
    """비디오 목록 조회 테스트"""
    print("\n📋 비디오 목록 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/videos")
        print(f"상태 코드: {response.status_code}")
        if response.status_code == 200:
            videos = response.json()
            print(f"✅ 비디오 {len(videos)}개 발견:")
            for video in videos:
                print(f"  - {video['drama_name']} {video['episode_number']} (ID: {video['id']})")
        else:
            print(f"❌ 비디오 목록 조회 실패: {response.text}")
    except Exception as e:
        print(f"❌ 오류: {e}")

def test_vector_search():
    """벡터 검색 테스트"""
    print("\n🔍 벡터 검색 테스트...")
    
    # 랜덤 임베딩 벡터 생성 (384차원)
    query_embedding = np.random.rand(384).tolist()
    
    search_data = {
        "query_embedding": query_embedding,
        "node_type": "object",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/search/vector", json=search_data)
        print(f"상태 코드: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 검색 결과 {len(results)}개:")
            for result in results:
                print(f"  - {result.get('label', 'N/A')} (유사도: {result.get('similarity', 0):.3f})")
        else:
            print(f"❌ 벡터 검색 실패: {response.text}")
    except Exception as e:
        print(f"❌ 오류: {e}")

def test_hybrid_search():
    """하이브리드 검색 테스트"""
    print("\n🔍 하이브리드 검색 테스트...")
    
    # 랜덤 임베딩 벡터 생성
    query_embedding = np.random.rand(384).tolist()
    
    search_data = {
        "query_text": "walk",
        "query_embedding": query_embedding,
        "node_type": None,  # 모든 타입에서 검색
        "top_k": 5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/search/hybrid", json=search_data)
        print(f"상태 코드: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 하이브리드 검색 결과 {len(results)}개:")
            for result in results:
                print(f"  - [{result.get('node_type', 'N/A')}] {result.get('label', 'N/A')} (유사도: {result.get('similarity', 0):.3f})")
        else:
            print(f"❌ 하이브리드 검색 실패: {response.text}")
    except Exception as e:
        print(f"❌ 오류: {e}")

def main():
    """메인 테스트 함수"""
    print("🚀 Scene Graph Database API 테스트 시작")
    print("=" * 50)
    
    # 1. 헬스 체크
    if not test_health_check():
        print("❌ API 서버가 실행되지 않았습니다. 서버를 먼저 시작해주세요.")
        return
    
    # 2. 비디오 생성
    video_id = test_create_video()
    
    # 3. 비디오 목록 조회
    test_list_videos()
    
    # 4. 벡터 검색 (데이터가 있을 때만)
    test_vector_search()
    
    # 5. 하이브리드 검색 (데이터가 있을 때만)
    test_hybrid_search()
    
    print("\n" + "=" * 50)
    print("✅ API 테스트 완료")
    
    if video_id:
        print(f"💡 생성된 비디오 ID: {video_id}")
        print("💡 이제 장면 데이터를 추가하여 더 많은 테스트를 할 수 있습니다.")

if __name__ == "__main__":
    main()

