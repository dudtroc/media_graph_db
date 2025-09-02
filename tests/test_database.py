#!/usr/bin/env python3
"""
데이터베이스 테스트 스크립트 (API를 통한 접근)
"""

import os
import sys
import json
import requests

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_api_connection():
    """API 서버 연결 테스트"""
    print("🔍 API 서버 연결 테스트...")
    
    api_base_url = os.getenv('API_URL', 'http://localhost:8000')
    
    try:
        response = requests.get(f"{api_base_url}/health")
        if response.status_code == 200:
            print("✅ API 서버 연결 성공")
            return True
        else:
            print(f"❌ API 서버 연결 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API 서버 연결 실패: {e}")
        return False

def test_video_operations(api_base_url):
    """비디오 관련 작업 테스트"""
    print("\n🎬 비디오 작업 테스트...")
    
    try:
        # 비디오 생성
        video_data = {
            "video_unique_id": 1001,
            "drama_name": "Kingdom",
            "episode_number": "EP01"
        }
        
        response = requests.post(f"{api_base_url}/videos", json=video_data)
        if response.status_code == 200:
            result = response.json()
            video_id = result.get('video_id')
            print(f"✅ 비디오 생성 성공: ID {video_id}")
            
            # 동일한 비디오 재생성 (업데이트)
            response = requests.post(f"{api_base_url}/videos", json=video_data)
            if response.status_code == 200:
                result = response.json()
                video_id2 = result.get('video_id')
                print(f"✅ 비디오 업데이트 성공: ID {video_id2}")
                return video_id
            else:
                print(f"❌ 비디오 업데이트 실패: {response.text}")
                return None
        else:
            print(f"❌ 비디오 생성 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 비디오 작업 실패: {e}")
        return None

def test_scene_operations(api_base_url, video_unique_id):
    """장면 관련 작업 테스트"""
    print("\n🎭 장면 작업 테스트...")
    
    try:
        # 테스트 데이터 파일 경로
        json_file = "tests/data/Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json"
        
        if os.path.exists(json_file):
            # JSON 데이터 로드
            with open(json_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            
            # 장면 데이터 준비
            scene_payload = {
                "video_unique_id": video_unique_id,
                "scene_data": {
                    "scene_number": "2220-3134",
                    "scene_place": scene_data.get('scene_graph', {}).get('meta', {}).get('scene_place', '테스트 장소'),
                    "scene_time": scene_data.get('scene_graph', {}).get('meta', {}).get('scene_time', '테스트 시간'),
                    "scene_atmosphere": scene_data.get('scene_graph', {}).get('meta', {}).get('scene_atmosphere', '테스트 분위기')
                },
                "pt_data": {
                    "z": [[0.1, 0.2, 0.3]],  # 간단한 임베딩 벡터
                    "orig_id": ["test_node_1"]
                }
            }
            
            # 장면 데이터 삽입
            response = requests.post(f"{api_base_url}/scenes", json=scene_payload)
            if response.status_code == 200:
                result = response.json()
                scene_id = result.get('scene_id')
                print(f"✅ 장면 데이터 삽입 성공: ID {scene_id}")
                return scene_id
            else:
                print(f"❌ 장면 데이터 삽입 실패: {response.text}")
                return None
        else:
            print("⚠️ 테스트 데이터 파일을 찾을 수 없습니다.")
            print(f"JSON 파일: {json_file}")
            return None
            
    except Exception as e:
        print(f"❌ 장면 작업 실패: {e}")
        return None

def test_search_operations(api_base_url):
    """검색 작업 테스트"""
    print("\n🔍 검색 작업 테스트...")
    
    try:
        # 랜덤 임베딩 벡터 생성
        import numpy as np
        query_embedding = np.random.rand(384).tolist()
        
        # 벡터 검색 테스트
        search_data = {
            "query_embedding": query_embedding,
            "node_type": "object",
            "top_k": 3
        }
        
        response = requests.post(f"{api_base_url}/search/vector", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 벡터 검색 성공: {len(results)}개 결과")
        else:
            print(f"❌ 벡터 검색 실패: {response.text}")
        
        # 하이브리드 검색 테스트
        hybrid_search_data = {
            "query_text": "walk",
            "query_embedding": query_embedding,
            "node_type": None,
            "top_k": 5
        }
        
        response = requests.post(f"{api_base_url}/search/hybrid", json=hybrid_search_data)
        if response.status_code == 200:
            hybrid_results = response.json()
            print(f"✅ 하이브리드 검색 성공: {len(hybrid_results)}개 결과")
        else:
            print(f"❌ 하이브리드 검색 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 검색 작업 실패: {e}")

def test_scene_graph_retrieval(api_base_url, scene_id):
    """장면 그래프 정보 조회 테스트"""
    print("\n🎭 장면 그래프 정보 조회 테스트...")
    
    try:
        response = requests.get(f"{api_base_url}/scenes/{scene_id}")
        if response.status_code == 200:
            scene_graph = response.json()
            print(f"✅ 장면 그래프 조회 성공")
            print(f"  - 장면 ID: {scene_graph.get('scene', {}).get('id')}")
            print(f"  - 객체 수: {len(scene_graph.get('objects', []))}")
            print(f"  - 이벤트 수: {len(scene_graph.get('events', []))}")
            print(f"  - 공간 관계 수: {len(scene_graph.get('spatial', []))}")
            print(f"  - 시간 관계 수: {len(scene_graph.get('temporal', []))}")
        else:
            print(f"❌ 장면 그래프 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 장면 그래프 조회 실패: {e}")

def test_video_summary(api_base_url, video_unique_id):
    """비디오 요약 정보 조회 테스트"""
    print("\n📊 비디오 요약 정보 조회 테스트...")
    
    try:
        response = requests.get(f"{api_base_url}/videos/{video_unique_id}/summary")
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ 비디오 요약 조회 성공")
            print(f"  - 드라마: {summary.get('drama_name')}")
            print(f"  - 에피소드: {summary.get('episode_number')}")
            print(f"  - 장면 수: {summary.get('scene_count')}")
            print(f"  - 객체 수: {summary.get('object_count')}")
            print(f"  - 이벤트 수: {summary.get('event_count')}")
        else:
            print(f"❌ 비디오 요약 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 비디오 요약 조회 실패: {e}")

def main():
    """메인 테스트 함수"""
    print("🚀 데이터베이스 API 테스트 시작")
    print("=" * 50)
    
    api_base_url = os.getenv('API_URL', 'http://localhost:8000')
    print(f"🌐 API 서버: {api_base_url}")
    
    # 1. API 연결 테스트
    if not test_api_connection():
        print("❌ API 서버에 연결할 수 없어 테스트를 중단합니다.")
        return
    
    # 2. 비디오 작업 테스트
    video_unique_id = test_video_operations(api_base_url)
    if not video_unique_id:
        print("❌ 비디오 작업 테스트 실패로 중단합니다.")
        return
    
    # 3. 장면 작업 테스트
    scene_id = test_scene_operations(api_base_url, video_unique_id)
    if not scene_id:
        print("❌ 장면 작업 테스트 실패로 중단합니다.")
        return
    
    # 4. 검색 작업 테스트
    test_search_operations(api_base_url)
    
    # 5. 장면 그래프 조회 테스트
    test_scene_graph_retrieval(api_base_url, scene_id)
    
    # 6. 비디오 요약 조회 테스트
    test_video_summary(api_base_url, video_unique_id)
    
    print("\n🎉 모든 테스트가 완료되었습니다!")
    print("\n📝 참고: 이 테스트는 API를 통해서만 데이터베이스에 접근합니다.")
    print("   직접적인 데이터베이스 연결은 보안상 허용되지 않습니다.")

if __name__ == "__main__":
    main()
