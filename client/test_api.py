#!/usr/bin/env python3
"""
Scene Graph Database API 테스트 클라이언트
모든 데이터베이스 작업을 API를 통해 테스트
"""

import requests
import json
import os
import numpy as np
from typing import Dict, Any, List

# API 서버 기본 URL (환경 변수에서 가져오기)
BASE_URL = os.getenv("API_URL", "http://localhost:8000")

class SceneGraphAPIClient:
    """Scene Graph Database API 클라이언트"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """헬스 체크"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def create_video(self, video_unique_id: int, drama_name: str, episode_number: str) -> Dict[str, Any]:
        """비디오 생성"""
        video_data = {
            "video_unique_id": video_unique_id,
            "drama_name": drama_name,
            "episode_number": episode_number
        }
        
        response = self.session.post(f"{self.base_url}/videos", json=video_data)
        response.raise_for_status()
        return response.json()
    
    def create_scene(self, video_unique_id: int, scene_data: dict, pt_data: dict) -> Dict[str, Any]:
        """장면 데이터 생성"""
        scene_request = {
            "video_unique_id": video_unique_id,
            "scene_data": scene_data,
            "pt_data": pt_data
        }
        
        response = self.session.post(f"{self.base_url}/scenes", json=scene_request)
        response.raise_for_status()
        return response.json()
    
    def create_object(self, scene_id: int, object_id: str, super_type: str, type_of: str, 
                     label: str, attributes: dict = None) -> Dict[str, Any]:
        """객체 노드 생성"""
        object_data = {
            "scene_id": scene_id,
            "object_id": object_id,
            "super_type": super_type,
            "type_of": type_of,
            "label": label,
            "attributes": attributes or {}
        }
        
        response = self.session.post(f"{self.base_url}/objects", json=object_data)
        response.raise_for_status()
        return response.json()
    
    def create_event(self, scene_id: int, event_id: str, subject_id: str, verb: str, 
                    object_id: str = None, attributes: dict = None) -> Dict[str, Any]:
        """이벤트 노드 생성"""
        event_data = {
            "scene_id": scene_id,
            "event_id": event_id,
            "subject_id": subject_id,
            "verb": verb,
            "object_id": object_id,
            "attributes": attributes or {}
        }
        
        response = self.session.post(f"{self.base_url}/events", json=event_data)
        response.raise_for_status()
        return response.json()
    
    def create_spatial(self, scene_id: int, spatial_id: str, subject_id: str, 
                      predicate: str, object_id: str) -> Dict[str, Any]:
        """공간 관계 생성"""
        spatial_data = {
            "scene_id": scene_id,
            "spatial_id": spatial_id,
            "subject_id": subject_id,
            "predicate": predicate,
            "object_id": object_id
        }
        
        response = self.session.post(f"{self.base_url}/spatial", json=spatial_data)
        response.raise_for_status()
        return response.json()
    
    def create_temporal(self, scene_id: int, temporal_id: str, subject_id: str, 
                       predicate: str, object_id: str) -> Dict[str, Any]:
        """시간 관계 생성"""
        temporal_data = {
            "scene_id": scene_id,
            "temporal_id": temporal_id,
            "subject_id": subject_id,
            "predicate": predicate,
            "object_id": object_id
        }
        
        response = self.session.post(f"{self.base_url}/temporal", json=temporal_data)
        response.raise_for_status()
        return response.json()
    
    def vector_search(self, query_embedding: List[float], node_type: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """벡터 기반 유사도 검색"""
        search_query = {
            "query_embedding": query_embedding,
            "node_type": node_type,
            "top_k": top_k
        }
        
        response = self.session.post(f"{self.base_url}/search/vector", json=search_query)
        response.raise_for_status()
        return response.json()
    
    def hybrid_search(self, query_text: str, query_embedding: List[float], 
                     node_type: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """하이브리드 검색 (텍스트 + 벡터)"""
        search_query = {
            "query_text": query_text,
            "query_embedding": query_embedding,
            "node_type": node_type,
            "top_k": top_k
        }
        
        response = self.session.post(f"{self.base_url}/search/hybrid", json=search_query)
        response.raise_for_status()
        return response.json()
    
    def get_scene_graph(self, scene_id: int) -> Dict[str, Any]:
        """특정 장면의 그래프 정보 조회"""
        response = self.session.get(f"{self.base_url}/scenes/{scene_id}")
        response.raise_for_status()
        return response.json()
    
    def get_video_summary(self, video_unique_id: int) -> Dict[str, Any]:
        """비디오 요약 정보 조회"""
        response = self.session.get(f"{self.base_url}/videos/{video_unique_id}/summary")
        response.raise_for_status()
        return response.json()
    
    def list_videos(self) -> List[Dict[str, Any]]:
        """모든 비디오 목록 조회"""
        response = self.session.get(f"{self.base_url}/videos")
        response.raise_for_status()
        return response.json()

def test_health_check(client: SceneGraphAPIClient):
    """헬스 체크 테스트"""
    print("🔍 헬스 체크 테스트...")
    print(f"🌐 API 서버 URL: {client.base_url}")
    
    if client.health_check():
        print("✅ API 서버가 정상적으로 실행되고 있습니다.")
        return True
    else:
        print("❌ API 서버에 연결할 수 없습니다.")
        return False

def test_video_operations(client: SceneGraphAPIClient):
    """비디오 관련 작업 테스트"""
    print("\n🎬 비디오 작업 테스트...")
    
    try:
        # 비디오 생성
        result = client.create_video(1001, "Kingdom", "EP01")
        print(f"✅ 비디오 생성 성공: {result}")
        
        # 동일한 비디오 재생성 (업데이트)
        result2 = client.create_video(1001, "Kingdom", "EP01")
        print(f"✅ 비디오 업데이트 성공: {result2}")
        
        return result.get('video_id')
    except Exception as e:
        print(f"❌ 비디오 작업 실패: {e}")
        return None

def test_scene_operations(client: SceneGraphAPIClient, video_unique_id: int):
    """장면 관련 작업 테스트"""
    print("\n🎭 장면 작업 테스트...")
    
    try:
        # 간단한 테스트 데이터 생성
        scene_data = {
            "scene_number": "SC001",
            "start_time": "00:01:33",
            "end_time": "00:02:11",
            "description": "테스트 장면"
        }
        
        pt_data = {
            "features": np.random.rand(384).tolist(),
            "metadata": {"test": True}
        }
        
        # 장면 데이터 생성
        result = client.create_scene(video_unique_id, scene_data, pt_data)
        print(f"✅ 장면 데이터 생성 성공: {result}")
        
        return result.get('scene_id')
    except Exception as e:
        print(f"❌ 장면 작업 실패: {e}")
        return None

def test_node_operations(client: SceneGraphAPIClient, scene_id: int):
    """노드 생성 작업 테스트"""
    print("\n🔗 노드 생성 작업 테스트...")
    
    try:
        # 객체 노드 생성
        object_result = client.create_object(
            scene_id=scene_id,
            object_id="OBJ001",
            super_type="person",
            type_of="character",
            label="주인공",
            attributes={"age": 25, "gender": "male"}
        )
        print(f"✅ 객체 노드 생성 성공: {object_result}")
        
        # 이벤트 노드 생성
        event_result = client.create_event(
            scene_id=scene_id,
            event_id="EVT001",
            subject_id="OBJ001",
            verb="walk",
            attributes={"speed": "normal"}
        )
        print(f"✅ 이벤트 노드 생성 성공: {event_result}")
        
        # 공간 관계 생성
        spatial_result = client.create_spatial(
            scene_id=scene_id,
            spatial_id="SPA001",
            subject_id="OBJ001",
            predicate="near",
            object_id="OBJ002"
        )
        print(f"✅ 공간 관계 생성 성공: {spatial_result}")
        
        return True
    except Exception as e:
        print(f"❌ 노드 생성 작업 실패: {e}")
        return False

def test_search_operations(client: SceneGraphAPIClient):
    """검색 작업 테스트"""
    print("\n🔍 검색 작업 테스트...")
    
    try:
        # 랜덤 임베딩 벡터 생성
        query_embedding = np.random.rand(384).tolist()
        
        # 벡터 검색 테스트
        vector_results = client.vector_search(query_embedding, 'object', top_k=3)
        print(f"✅ 벡터 검색 성공: {len(vector_results)}개 결과")
        
        # 하이브리드 검색 테스트
        hybrid_results = client.hybrid_search("walk", query_embedding, top_k=5)
        print(f"✅ 하이브리드 검색 성공: {len(hybrid_results)}개 결과")
        
        return True
    except Exception as e:
        print(f"❌ 검색 작업 실패: {e}")
        return False

def test_data_retrieval(client: SceneGraphAPIClient, video_unique_id: int, scene_id: int):
    """데이터 조회 테스트"""
    print("\n📊 데이터 조회 테스트...")
    
    try:
        # 장면 그래프 조회
        if scene_id:
            scene_graph = client.get_scene_graph(scene_id)
            print(f"✅ 장면 그래프 조회 성공:")
            print(f"  - 장면 ID: {scene_id}")
            if 'objects' in scene_graph:
                print(f"  - 객체 수: {len(scene_graph['objects'])}")
            if 'events' in scene_graph:
                print(f"  - 이벤트 수: {len(scene_graph['events'])}")
        
        # 비디오 요약 조회
        video_summary = client.get_video_summary(video_unique_id)
        print(f"✅ 비디오 요약 조회 성공:")
        print(f"  - 비디오: {video_summary.get('drama_name')} {video_summary.get('episode_number')}")
        
        # 비디오 목록 조회
        videos = client.list_videos()
        print(f"✅ 비디오 목록 조회 성공: {len(videos)}개 비디오")
        
        return True
    except Exception as e:
        print(f"❌ 데이터 조회 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Scene Graph Database API 테스트 시작")
    print("=" * 50)
    
    # API 클라이언트 생성
    client = SceneGraphAPIClient()
    
    # 1. 헬스 체크
    if not test_health_check(client):
        print("❌ API 서버가 실행되지 않았습니다. 서버를 먼저 시작해주세요.")
        return
    
    try:
        # 2. 비디오 작업
        video_unique_id = 1001
        test_video_operations(client)
        
        # 3. 장면 작업
        scene_id = test_scene_operations(client, video_unique_id)
        
        # 4. 노드 생성 작업
        if scene_id:
            test_node_operations(client, scene_id)
        
        # 5. 검색 작업
        test_search_operations(client)
        
        # 6. 데이터 조회
        test_data_retrieval(client, video_unique_id, scene_id)
        
        print("\n" + "=" * 50)
        print("✅ 모든 API 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

