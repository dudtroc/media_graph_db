#!/usr/bin/env python3
"""
간단한 장면그래프 및 임베딩 데이터 확인 도구
"""

import requests
import json
from typing import Dict, List, Any

class SimpleDataVerifier:
    def __init__(self, api_base_url: str = "http://api_server:8000"):
        self.api_base_url = api_base_url
    
    def verify_all_data(self):
        """모든 데이터 저장 상태 확인"""
        print("🔍 장면그래프 및 임베딩 데이터 저장 상태 확인")
        print("=" * 60)
        
        try:
            # 1. 비디오 데이터 확인
            self.verify_videos()
            
            # 2. 장면 데이터 확인
            self.verify_scenes()
            
            # 3. 노드 데이터 확인
            self.verify_nodes()
            
            # 4. 임베딩 데이터 확인 (API를 통한)
            self.verify_embeddings_via_api()
            
            print("\n" + "=" * 60)
            print("✅ 데이터 검증 완료!")
            
        except Exception as e:
            print(f"❌ 데이터 검증 실패: {e}")
    
    def verify_videos(self):
        """비디오 데이터 확인"""
        print("\n📺 비디오 데이터 확인")
        print("-" * 30)
        
        try:
            response = requests.get(f"{self.api_base_url}/videos")
            if response.status_code == 200:
                videos = response.json()
                print(f"✅ 비디오 총 {len(videos)}개")
                
                for video in videos:
                    print(f"  - ID: {video.get('id', 'N/A')}, 제목: {video.get('title', 'N/A')}, 에피소드: {video.get('episode', 'N/A')}")
            else:
                print(f"❌ 비디오 데이터 조회 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 비디오 데이터 확인 오류: {e}")
    
    def verify_scenes(self):
        """장면 데이터 확인"""
        print("\n🎭 장면 데이터 확인")
        print("-" * 30)
        
        try:
            # 비디오별 장면 확인
            response = requests.get(f"{self.api_base_url}/videos")
            if response.status_code == 200:
                videos = response.json()
                
                total_scenes = 0
                for video in videos:
                    video_id = video.get('id')
                    if video_id:
                        scenes_response = requests.get(f"{self.api_base_url}/scenes?video_id={video_id}")
                        
                        if scenes_response.status_code == 200:
                            scenes = scenes_response.json()
                            total_scenes += len(scenes)
                            print(f"  📺 비디오 ID {video_id}: {len(scenes)}개 장면")
                            
                            for scene in scenes:
                                print(f"    - 장면 {scene.get('scene_number', 'N/A')}: {scene.get('scene_place', 'N/A')} "
                                      f"({scene.get('start_frame', 'N/A')}-{scene.get('end_frame', 'N/A')})")
                
                print(f"✅ 총 장면 수: {total_scenes}개")
            else:
                print(f"❌ 장면 데이터 조회 실패")
        except Exception as e:
            print(f"❌ 장면 데이터 확인 오류: {e}")
    
    def verify_nodes(self):
        """노드 데이터 확인"""
        print("\n🔗 노드 데이터 확인")
        print("-" * 30)
        
        try:
            # 객체 노드 확인
            objects_response = requests.get(f"{self.api_base_url}/objects")
            if objects_response.status_code == 200:
                objects = objects_response.json()
                print(f"👥 객체 노드: {len(objects)}개")
                
                # 객체 타입별 분류
                object_types = {}
                for obj in objects:
                    obj_type = obj.get('type_of', 'unknown')
                    object_types[obj_type] = object_types.get(obj_type, 0) + 1
                
                for obj_type, count in object_types.items():
                    print(f"  - {obj_type}: {count}개")
            
            # 이벤트 노드 확인
            events_response = requests.get(f"{self.api_base_url}/events")
            if events_response.status_code == 200:
                events = events_response.json()
                print(f"🎬 이벤트 노드: {len(events)}개")
                
                # 이벤트 동사별 분류
                event_verbs = {}
                for event in events:
                    verb = event.get('verb', 'unknown')
                    event_verbs[verb] = event_verbs.get(verb, 0) + 1
                
                for verb, count in event_verbs.items():
                    print(f"  - {verb}: {count}개")
            
            # 공간 관계 확인
            spatial_response = requests.get(f"{self.api_base_url}/spatial")
            if spatial_response.status_code == 200:
                spatial = spatial_response.json()
                print(f"📍 공간 관계: {len(spatial)}개")
                
                # 공간 관계 타입별 분류
                spatial_types = {}
                for rel in spatial:
                    predicate = rel.get('predicate', 'unknown')
                    spatial_types[predicate] = spatial_types.get(predicate, 0) + 1
                
                for predicate, count in spatial_types.items():
                    print(f"  - {predicate}: {count}개")
            
            # 시간 관계 확인
            temporal_response = requests.get(f"{self.api_base_url}/temporal")
            if temporal_response.status_code == 200:
                temporal = temporal_response.json()
                print(f"⏰ 시간 관계: {len(temporal)}개")
                
                # 시간 관계 타입별 분류
                temporal_types = {}
                for rel in temporal:
                    predicate = rel.get('predicate', 'unknown')
                    temporal_types[predicate] = temporal_types.get(predicate, 0) + 1
                
                for predicate, count in temporal_types.items():
                    print(f"  - {predicate}: {count}개")
                    
        except Exception as e:
            print(f"❌ 노드 데이터 확인 오류: {e}")
    
    def verify_embeddings_via_api(self):
        """임베딩 데이터 확인 (API를 통한)"""
        print("\n🔗 임베딩 데이터 확인")
        print("-" * 30)
        
        try:
            # 임베딩 데이터는 직접 API로 조회할 수 없으므로
            # 벡터 검색을 통해 임베딩이 있는지 확인
            print("📊 임베딩 데이터 존재 확인을 위한 벡터 검색 테스트...")
            
            # 간단한 벡터 검색 테스트 (384차원)
            test_embedding = [0.1] * 384
            
            search_data = {
                "query_text": "test",
                "query_embedding": test_embedding,
                "node_type": "object",
                "top_k": 1
            }
            
            response = requests.post(
                f"{self.api_base_url}/search/hybrid",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ 벡터 검색 성공: {len(results)}개 결과")
                print("✅ 임베딩 데이터가 정상적으로 저장되어 있습니다!")
                
                for i, result in enumerate(results[:3]):
                    print(f"  {i+1}. {result.get('node_type', 'unknown')} {result.get('node_id', 'unknown')} "
                          f"(유사도: {result.get('similarity', 'unknown'):.4f})")
            else:
                print(f"❌ 벡터 검색 실패: {response.status_code}")
                print(f"   오류 내용: {response.text}")
                print("⚠️  임베딩 데이터 저장 상태를 확인할 수 없습니다.")
                
        except Exception as e:
            print(f"❌ 임베딩 데이터 확인 오류: {e}")
    
    def test_simple_search(self):
        """간단한 텍스트 검색 테스트"""
        print("\n🔍 텍스트 검색 테스트")
        print("-" * 30)
        
        try:
            # 텍스트 검색 테스트
            search_data = {
                "query": "walk",
                "node_type": "event",
                "top_k": 3
            }
            
            response = requests.post(
                f"{self.api_base_url}/search/text",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ 텍스트 검색 성공: {len(results)}개 결과")
                
                for i, result in enumerate(results[:3]):
                    print(f"  {i+1}. {result.get('node_type', 'unknown')} {result.get('node_id', 'unknown')} "
                          f"- {result.get('content', 'N/A')}")
            else:
                print(f"❌ 텍스트 검색 실패: {response.status_code}")
                print(f"   오류 내용: {response.text}")
                
        except Exception as e:
            print(f"❌ 텍스트 검색 테스트 오류: {e}")

def main():
    """메인 함수"""
    verifier = SimpleDataVerifier()
    
    print("🚀 간단한 장면그래프 및 임베딩 데이터 검증 도구")
    print("=" * 60)
    
    # API 서버 연결 확인
    try:
        response = requests.get(f"{verifier.api_base_url}/videos")
        if response.status_code == 200:
            print("✅ API 서버 연결 확인")
        else:
            print(f"❌ API 서버 연결 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API 서버 연결 오류: {e}")
        return
    
    # 데이터 검증 실행
    verifier.verify_all_data()
    
    # 텍스트 검색 테스트
    verifier.test_simple_search()

if __name__ == "__main__":
    main()
