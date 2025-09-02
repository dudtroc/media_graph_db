#!/usr/bin/env python3
"""
장면그래프와 임베딩 데이터 저장 상태 확인 도구
"""

import requests
import json
from typing import Dict, List, Any

class DataVerifier:
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
            
            # 4. 임베딩 데이터 확인
            self.verify_embeddings()
            
            # 5. 데이터 매핑 확인
            self.verify_data_mapping()
            
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
                    print(f"  - ID: {video['id']}, 제목: {video['title']}, 에피소드: {video['episode']}")
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
                    video_id = video['id']
                    scenes_response = requests.get(f"{self.api_base_url}/scenes?video_id={video_id}")
                    
                    if scenes_response.status_code == 200:
                        scenes = scenes_response.json()
                        total_scenes += len(scenes)
                        print(f"  📺 {video['title']} {video['episode']}: {len(scenes)}개 장면")
                        
                        for scene in scenes:
                            print(f"    - 장면 {scene['scene_number']}: {scene['scene_place']} ({scene['start_frame']}-{scene['end_frame']})")
                
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
    
    def verify_embeddings(self):
        """임베딩 데이터 확인"""
        print("\n🔗 임베딩 데이터 확인")
        print("-" * 30)
        
        try:
            # 임베딩 데이터 조회 (직접 DB 쿼리)
            import subprocess
            
            # PostgreSQL에서 임베딩 데이터 조회
            cmd = [
                "docker", "exec", "-i", "scene_graph_postgres",
                "psql", "-U", "postgres", "-d", "scene_graph_db", "-t", "-c",
                """
                SELECT 
                    node_type,
                    COUNT(*) as count,
                    vector_dims(embedding) as embedding_dim
                FROM embeddings 
                GROUP BY node_type, vector_dims(embedding)
                ORDER BY node_type;
                """
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                total_embeddings = 0
                
                for line in lines:
                    if line.strip():
                        parts = line.strip().split('|')
                        if len(parts) >= 3:
                            node_type = parts[0].strip()
                            count = int(parts[1].strip())
                            dim = parts[2].strip()
                            total_embeddings += count
                            print(f"  {node_type}: {count}개 (차원: {dim})")
                
                print(f"✅ 총 임베딩 수: {total_embeddings}개")
                
                # 임베딩 샘플 확인
                cmd_sample = [
                    "docker", "exec", "-i", "scene_graph_postgres",
                    "psql", "-U", "postgres", "-d", "scene_graph_db", "-t", "-c",
                    """
                    SELECT node_id, node_type, 
                           array_to_string(embedding[1:5], ',') as sample_embedding
                    FROM embeddings 
                    LIMIT 3;
                    """
                ]
                
                result_sample = subprocess.run(cmd_sample, capture_output=True, text=True)
                if result_sample.returncode == 0:
                    print("\n📊 임베딩 샘플 (처음 5차원):")
                    for line in result_sample.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.strip().split('|')
                            if len(parts) >= 3:
                                node_id = parts[0].strip()
                                node_type = parts[1].strip()
                                sample = parts[2].strip()
                                print(f"  {node_type} {node_id}: [{sample}]")
            else:
                print(f"❌ 임베딩 데이터 조회 실패: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 임베딩 데이터 확인 오류: {e}")
    
    def verify_data_mapping(self):
        """데이터 매핑 확인"""
        print("\n🔍 데이터 매핑 확인")
        print("-" * 30)
        
        try:
            # JSON 파일의 노드 ID와 DB의 노드 ID 매핑 확인
            import subprocess
            
            # DB에서 모든 노드 ID 수집
            cmd = [
                "docker", "exec", "-i", "scene_graph_postgres",
                "psql", "-U", "postgres", "-d", "scene_graph_db", "-t", "-c",
                """
                SELECT 'object' as type, object_id as id FROM objects
                UNION ALL
                SELECT 'event' as type, event_id as id FROM events
                UNION ALL
                SELECT 'spatial' as type, spatial_id as id FROM spatial
                UNION ALL
                SELECT 'temporal' as type, temporal_id as id FROM temporal
                ORDER BY type, id;
                """
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                db_nodes = {}
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split('|')
                        if len(parts) >= 2:
                            node_type = parts[0].strip()
                            node_id = int(parts[1].strip())
                            if node_type not in db_nodes:
                                db_nodes[node_type] = []
                            db_nodes[node_type].append(node_id)
                
                print("📊 DB에 저장된 노드 ID:")
                for node_type, ids in db_nodes.items():
                    print(f"  {node_type}: {sorted(ids)}")
                
                # 임베딩이 있는 노드 ID 확인
                cmd_emb = [
                    "docker", "exec", "-i", "scene_graph_postgres",
                    "psql", "-U", "postgres", "-d", "scene_graph_db", "-t", "-c",
                    """
                    SELECT node_type, node_id FROM embeddings ORDER BY node_type, node_id;
                    """
                ]
                
                result_emb = subprocess.run(cmd_emb, capture_output=True, text=True)
                if result_emb.returncode == 0:
                    embedding_nodes = {}
                    for line in result_emb.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.strip().split('|')
                            if len(parts) >= 2:
                                node_type = parts[0].strip()
                                node_id = int(parts[1].strip())
                                if node_type not in embedding_nodes:
                                    embedding_nodes[node_type] = []
                                embedding_nodes[node_type].append(node_id)
                    
                    print("\n🔗 임베딩이 있는 노드 ID:")
                    for node_type, ids in embedding_nodes.items():
                        print(f"  {node_type}: {sorted(ids)}")
                    
                    # 매핑 상태 확인
                    print("\n📈 매핑 상태:")
                    for node_type in db_nodes:
                        db_ids = set(db_nodes[node_type])
                        emb_ids = set(embedding_nodes.get(node_type, []))
                        
                        matched = db_ids.intersection(emb_ids)
                        unmatched_db = db_ids - emb_ids
                        unmatched_emb = emb_ids - db_ids
                        
                        print(f"  {node_type}:")
                        print(f"    ✅ 매칭: {len(matched)}개")
                        if unmatched_db:
                            print(f"    ❌ DB만 있음: {sorted(unmatched_db)}")
                        if unmatched_emb:
                            print(f"    ❌ 임베딩만 있음: {sorted(unmatched_emb)}")
            else:
                print(f"❌ 데이터 매핑 확인 실패: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 데이터 매핑 확인 오류: {e}")
    
    def test_vector_search(self):
        """벡터 검색 테스트"""
        print("\n🔍 벡터 검색 테스트")
        print("-" * 30)
        
        try:
            # 간단한 벡터 검색 테스트
            test_embedding = [0.1] * 384  # 384차원 테스트 벡터
            
            search_data = {
                "query_text": "test",
                "query_embedding": test_embedding,
                "node_type": None,
                "top_k": 3
            }
            
            response = requests.post(
                f"{self.api_base_url}/search/hybrid",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ 벡터 검색 성공: {len(results)}개 결과")
                
                for i, result in enumerate(results[:3]):
                    print(f"  {i+1}. {result.get('node_type', 'unknown')} {result.get('node_id', 'unknown')} "
                          f"(유사도: {result.get('similarity', 'unknown'):.4f})")
            else:
                print(f"❌ 벡터 검색 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 벡터 검색 테스트 오류: {e}")

def main():
    """메인 함수"""
    verifier = DataVerifier()
    
    print("🚀 장면그래프 및 임베딩 데이터 검증 도구")
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
    
    # 벡터 검색 테스트
    verifier.test_vector_search()

if __name__ == "__main__":
    main()
