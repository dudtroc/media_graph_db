#!/usr/bin/env python3
"""
장면그래프 데이터베이스 통합 클라이언트
모든 DB API 접근 기능을 통합한 클래스
"""

import os
import json
import requests
import torch
import torch.nn.functional as F
import heapq
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# 기존 클라이언트 모듈들 import
from util import VideoDataDeleter, SceneGraphDataChecker, SceneGraphAPIUploader
from util.schema_info import SchemaInfoChecker

# 환경 변수 로드
load_dotenv()

class SceneGraphDBClient:
    """
    장면그래프 데이터베이스 통합 클라이언트
    
    이 클래스는 다음 기능들을 통합합니다:
    - 비디오 데이터 삭제 (VideoDataDeleter)
    - 저장된 데이터 확인 (SceneGraphDataChecker)  
    - 장면그래프 데이터 업로드 (SceneGraphAPIUploader)
    - 기본적인 DB API 접근 기능
    """
    
    def __init__(self, db_api_base_url: str = None):
        """
        초기화
        
        Args:
            db_api_base_url: API 서버 URL (기본값: 환경변수 API_URL 또는 http://localhost:8000)
        """
        self.db_api_base_url = db_api_base_url or os.getenv("API_URL", "http://localhost:8000")
        self.session = requests.Session()
        
        # 하위 클라이언트들 초기화
        self.deleter = VideoDataDeleter(self.db_api_base_url)
        self.checker = SceneGraphDataChecker(self.db_api_base_url)
        self.uploader = SceneGraphAPIUploader(self.db_api_base_url)
        self.schema_checker = SchemaInfoChecker()
        
        print(f"🌐 SceneGraphClient 초기화 완료 - API URL: {self.db_api_base_url}")
    
    # ==================== 기본 연결 및 상태 확인 ====================
    
    def health_check(self) -> bool:
        """API 서버 헬스 체크"""
        return self.checker.check_connection()
    
    def get_server_info(self) -> Dict[str, Any]:
        """서버 기본 정보 조회"""
        try:
            response = self.session.get(f"{self.db_api_base_url}/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 서버 정보 조회 실패: {e}")
            return {}
    
    # ==================== 비디오 관리 ====================
    
    def get_videos(self) -> List[Dict[str, Any]]:
        """저장된 비디오 목록 조회"""
        return self.checker.get_videos()
    
    def get_video_info(self, video_unique_id: int) -> Optional[Dict[str, Any]]:
        """특정 비디오의 상세 정보 조회"""
        return self.deleter.get_video_info(video_unique_id)
    
    def create_video(self, drama_name: str, episode_number: str, video_unique_id: int = None) -> Optional[Dict[str, Any]]:
        """비디오 생성"""
        try:
            if video_unique_id is None:
                video_unique_id = self._generate_video_id(drama_name, episode_number)
            
            video_data = {
                "video_unique_id": video_unique_id,
                "drama_name": drama_name,
                "episode_number": episode_number
            }
            
            response = self.session.post(f"{self.db_api_base_url}/videos", json=video_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 비디오 생성 실패: {e}")
            return None
    
    def delete_video(self, video_unique_id: int, confirm: bool = False) -> bool:
        """비디오 및 연결된 모든 데이터 삭제"""
        return self.deleter.delete_video(video_unique_id, confirm)
    
    def list_videos(self) -> None:
        """비디오 목록 표시"""
        self.deleter.list_videos()
    
    # ==================== 장면 관리 ====================
    
    def get_scenes(self, video_id: int) -> List[Dict[str, Any]]:
        """특정 비디오의 장면 목록 조회"""
        return self.checker.get_scenes(video_id)
    
    def get_scene_graph(self, scene_id: int) -> Dict[str, Any]:
        """특정 장면의 완전한 그래프 정보 조회"""
        return self.checker.get_scene_graph(scene_id)
    
    def get_scene_objects(self, scene_id: int) -> List[Dict[str, Any]]:
        """특정 장면의 객체 노드 조회"""
        return self.checker.get_objects(scene_id)
    
    def get_scene_events(self, scene_id: int) -> List[Dict[str, Any]]:
        """특정 장면의 이벤트 노드 조회"""
        return self.checker.get_events(scene_id)
    
    def get_scene_spatial_relations(self, scene_id: int) -> List[Dict[str, Any]]:
        """특정 장면의 공간관계 조회"""
        return self.checker.get_spatial_relations(scene_id)
    
    def get_scene_temporal_relations(self, scene_id: int) -> List[Dict[str, Any]]:
        """특정 장면의 시간관계 조회"""
        return self.checker.get_temporal_relations(scene_id)
    
    def get_scene_embeddings(self, scene_id: int) -> List[Dict[str, Any]]:
        """특정 장면의 임베딩 정보 조회"""
        return self.checker.get_embeddings(scene_id)
    
    # ==================== 장면그래프 업로드 ====================
    
    def upload_scene_graph(self, json_file_path: str) -> bool:
        """
        JSON 파일과 대응하는 PT 파일을 이용하여 장면그래프 데이터를 업로드
        
        Args:
            json_file_path: JSON 파일 경로
            
        Returns:
            bool: 업로드 성공 여부
        """
        try:
            print(f"🚀 장면그래프 파일 업로드 시작: {json_file_path}")
            print("=" * 50)
            
            # 1. API 서버 헬스 체크
            if not self.health_check():
                print("❌ API 서버에 연결할 수 없습니다.")
                return False
            
            # 2. 파일명 파싱
            file_info = self._parse_filename(os.path.basename(json_file_path))
            drama_name = file_info['drama_name']
            episode_number = file_info['episode_number']
            start_frame = file_info['start_frame']
            end_frame = file_info['end_frame']
            
            print(f"📺 비디오 정보: {drama_name} {episode_number}")
            print(f"🎬 프레임 범위: {start_frame}-{end_frame}")
            
            # 3. JSON 파일 로드
            scene_data = self._load_scene_graph_data(json_file_path)
            
            # 4. 대응하는 PT 파일 찾기
            pt_file_path = json_file_path.replace('.json', '.pt')
            if not os.path.exists(pt_file_path):
                print(f"❌ 대응하는 PT 파일을 찾을 수 없습니다: {pt_file_path}")
                return False
            
            # 5. PT 파일 로드
            pt_data = self._load_pt_data(pt_file_path)
            
            # 6. 비디오 생성/조회
            video_result = self.create_video(drama_name, episode_number)
            if not video_result:
                print("❌ 비디오 생성 실패")
                return False
            
            video_id = video_result.get('video_id')
            actual_video_unique_id = video_result.get('video_unique_id')
            print(f"✅ 비디오 준비 완료: {drama_name} {episode_number} (ID: {video_id})")
            
            # 7. 장면 메타데이터 생성
            scene_meta = scene_data.get('scene_graph', {}).get('meta', {})
            scene_payload = {
                "scene_number": f"{start_frame}-{end_frame}",
                "scene_place": scene_meta.get('scene_place'),
                "scene_time": scene_meta.get('scene_time'),
                "scene_atmosphere": scene_meta.get('scene_atmosphere'),
                "start_frame": start_frame,
                "end_frame": end_frame
            }
            
            # 8. 장면 생성 API 호출 (임베딩 없이)
            scene_request = {
                "video_unique_id": actual_video_unique_id,
                "scene_data": scene_payload,
                "pt_data": None  # 임베딩은 나중에 처리
            }
            
            response = self.session.post(f"{self.db_api_base_url}/scenes", json=scene_request)
            response.raise_for_status()
            scene_result = response.json()
            scene_id = scene_result.get('scene_id')
            
            if not scene_id:
                print("❌ 장면 생성 실패")
                return False
            
            print(f"✅ 장면 생성 완료: {scene_id}")
            
            # 9. 노드 데이터 저장 (objects, events, spatial, temporal)
            self._create_nodes_from_data(scene_id, scene_data.get('scene_graph', {}), actual_video_unique_id)
            
            # 10. 임베딩 데이터 저장
            self._create_embeddings_from_pt_data(scene_id, pt_data, actual_video_unique_id)
            
            print("\n" + "=" * 50)
            print("✅ 장면그래프 데이터 업로드 완료!")
            print(f"📺 비디오: {drama_name} {episode_number}")
            print(f"🎭 장면: 프레임 {start_frame}-{end_frame}")
            print(f"🆔 비디오 ID: {video_id}, 장면 ID: {scene_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return False
    
    def upload_scene_graph_with_pt(self, scene_data: Dict[str, Any], embedding_info: Dict[str, Any], 
                                 video_unique_id: int, drama_name: str, episode_number: str,
                                 start_frame: int, end_frame: int) -> bool:
        """
        장면그래프 데이터와 임베딩 정보를 직접 입력받아 업로드
        
        Args:
            scene_data: 장면그래프 JSON 데이터
            embedding_info: 임베딩 정보 {'node_info': [...], 'node_embeddings': [...]}
            video_unique_id: 비디오 고유 ID
            drama_name: 드라마명
            episode_number: 에피소드 번호
            start_frame: 시작 프레임
            end_frame: 종료 프레임
        
        Returns:
            bool: 업로드 성공 여부
        """
        try:
            print("🚀 장면그래프 데이터 직접 업로드 시작")
            print("=" * 50)
            
            # 1. API 서버 헬스 체크
            if not self.health_check():
                print("❌ API 서버에 연결할 수 없습니다.")
                return False
            
            # 2. 비디오 생성/조회
            video_result = self.create_video(drama_name, episode_number, video_unique_id)
            if not video_result:
                print("❌ 비디오 생성 실패")
                return False
            
            video_id = video_result.get('video_id')
            actual_video_unique_id = video_result.get('video_unique_id')
            print(f"✅ 비디오 준비 완료: {drama_name} {episode_number} (ID: {video_id})")
            
            # 3. 장면 메타데이터 생성 (임베딩 제외)
            scene_meta = scene_data.get('scene_graph', {}).get('meta', {})
            scene_payload = {
                "scene_number": f"{start_frame}-{end_frame}",
                "scene_place": scene_meta.get('scene_place'),
                "scene_time": scene_meta.get('scene_time'),
                "scene_atmosphere": scene_meta.get('scene_atmosphere'),
                "start_frame": start_frame,
                "end_frame": end_frame
            }
            
            # 장면 생성 API 호출 (임베딩 없이)
            scene_request = {
                "video_unique_id": actual_video_unique_id,
                "scene_data": scene_payload,
                "pt_data": None  # 임베딩은 나중에 처리
            }
            
            response = self.session.post(f"{self.db_api_base_url}/scenes", json=scene_request)
            response.raise_for_status()
            scene_result = response.json()
            scene_id = scene_result.get('scene_id')
            
            if not scene_id:
                print("❌ 장면 생성 실패")
                return False
            
            print(f"✅ 장면 생성 완료: {scene_id}")
            
            # 4. 노드 데이터 저장 (objects, events, spatial, temporal)
            self._create_nodes_from_data(scene_id, scene_data.get('scene_graph', {}), actual_video_unique_id)
            
            # 5. 임베딩 데이터 저장
            self._create_embeddings_from_info(scene_id, embedding_info, actual_video_unique_id)
            
            print("\n" + "=" * 50)
            print("✅ 장면그래프 데이터 업로드 완료!")
            print(f"📺 비디오: {drama_name} {episode_number}")
            print(f"🎭 장면: 프레임 {start_frame}-{end_frame}")
            print(f"🆔 비디오 ID: {video_id}, 장면 ID: {scene_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return False
    
    # ==================== 내부 헬퍼 메서드 ====================
    
    def _parse_filename(self, filename: str) -> Dict[str, Any]:
        """
        파일명에서 비디오와 장면 정보 추출
        
        예시: "Hospital.Playlist_EP01_visual_181-455_(00_00_06-00_00_15)_meta_info.json"
        """
        import re
        
        print(f"📁 파일명 파싱: {filename}")
        
        # 파일명에서 정보 추출 (괄호와 번호 포함 처리)
        match = re.match(r'(.+)_(.+)_visual_(\d+)-(\d+)_.*_meta_info(?: \(\d+\))?\.json', filename)
        if not match:
            raise ValueError(f"파일명 형식이 올바르지 않습니다: {filename}")
        
        drama_name, episode_number, start_frame, end_frame = match.groups()
        
        result = {
            'drama_name': drama_name,
            'episode_number': episode_number,
            'start_frame': int(start_frame),
            'end_frame': int(end_frame)
        }
        
        print(f"✅ 파싱 결과: {result}")
        return result
    
    def _load_scene_graph_data(self, file_path: str) -> Dict[str, Any]:
        """JSON 파일에서 장면 그래프 데이터 로드"""
        print(f"📖 JSON 파일 로드: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON 데이터 로드 완료")
            return data
        except Exception as e:
            print(f"❌ JSON 파일 로드 실패: {e}")
            raise
    
    def _load_pt_data(self, file_path: str) -> Dict[str, Any]:
        """PT 파일에서 임베딩 데이터 로드"""
        print(f"📖 PT 파일 로드: {file_path}")
        
        try:
            import torch
            import numpy as np
            pt_data = torch.load(file_path, map_location='cpu')
            
            print(f"✅ PT 데이터 로드 완료")
            print(f"📊 PT 파일 키들: {list(pt_data.keys())}")
            
            # PyTorch 텐서를 JSON 직렬화 가능한 형태로 변환
            processed_data = {}
            for key, value in pt_data.items():
                if isinstance(value, torch.Tensor):
                    # 텐서를 numpy 배열로 변환 후 리스트로 변환
                    processed_data[key] = value.numpy().tolist()
                elif isinstance(value, (list, tuple)):
                    # 리스트나 튜플의 각 요소가 텐서인지 확인
                    processed_list = []
                    for item in value:
                        if isinstance(item, torch.Tensor):
                            processed_list.append(item.numpy().tolist())
                        else:
                            processed_list.append(item)
                    processed_data[key] = processed_list
                else:
                    processed_data[key] = value
            
            if 'z' in processed_data:
                embeddings = processed_data['z']
                if isinstance(embeddings, list) and len(embeddings) > 0:
                    print(f"✅ 임베딩 벡터 차원: {len(embeddings)} x {len(embeddings[0])}")
                else:
                    print(f"✅ 임베딩 타입: {type(embeddings)}")
            
            return processed_data
        except Exception as e:
            print(f"❌ PT 파일 로드 실패: {e}")
            raise
    
    def _create_embeddings_from_pt_data(self, scene_id: int, pt_data: Dict[str, Any], video_unique_id: int) -> None:
        """PT 데이터에서 임베딩 정보를 생성하여 저장"""
        print(f"🔗 PT 데이터에서 임베딩 생성 시작")
        
        try:
            if 'z' not in pt_data or 'orig_id' not in pt_data:
                print("❌ PT 데이터에 임베딩 정보가 없습니다.")
                return
            
            embeddings = pt_data['z']
            orig_ids = pt_data['orig_id']
            node_types = pt_data.get('node_type', [])
            
            if len(embeddings) != len(orig_ids):
                print(f"❌ 임베딩과 orig_id 개수가 일치하지 않음: {len(embeddings)} vs {len(orig_ids)}")
                return
            
            # ID 0은 특별한 노드이므로 건너뛰기
            for i, orig_id in enumerate(orig_ids):
                if orig_id == 0:
                    continue
                
                # 노드 타입 결정
                if i < len(node_types):
                    node_type_idx = node_types[i]
                    if node_type_idx == 0:
                        continue
                    elif node_type_idx == 1:
                        node_type = 'object'
                    elif node_type_idx == 2:
                        node_type = 'event'
                    elif node_type_idx == 3:
                        node_type = 'spatial'
                    else:
                        continue
                else:
                    # node_type 정보가 없으면 orig_id로 추정
                    if 1000 <= orig_id < 2000:
                        node_type = 'object'
                    elif 2000 <= orig_id < 3000:
                        node_type = 'temporal'
                    elif 3000 <= orig_id < 4000:
                        node_type = 'event'
                    elif 11000 <= orig_id < 12000:
                        node_type = 'spatial'
                    else:
                        continue
                
                # 실제 node_id 생성: {video_unique_id}_{scene_id}_{node_type}_{orig_id}
                actual_node_id = f"{video_unique_id}_{scene_id}_{node_type}_{orig_id}"
                
                # 임베딩 벡터 가져오기
                embedding_vector = embeddings[i]
                
                # 임베딩 데이터 저장
                embedding_data = {
                    "node_id": actual_node_id,
                    "node_type": node_type,
                    "embedding": embedding_vector
                }
                
                # 임베딩 저장 API 호출
                response = self.session.post(f"{self.db_api_base_url}/embeddings", json=embedding_data)
                response.raise_for_status()
                
                print(f"  ✅ 임베딩 저장: {node_type}_{orig_id} -> {actual_node_id}")
            
            print(f"✅ PT 데이터에서 임베딩 생성 완료: {len([id for id in orig_ids if id != 0])}개")
            
        except Exception as e:
            print(f"❌ PT 데이터 임베딩 생성 실패: {e}")
            raise
    
    def _create_nodes_from_data(self, scene_id: int, scene_graph: Dict[str, Any], video_unique_id: int) -> None:
        """장면그래프 데이터에서 노드들을 생성"""
        print(f"🔗 노드 데이터 저장 시작: Scene ID {scene_id}")
        
        try:
            # 1. 객체 노드 저장
            objects = scene_graph.get('objects', [])
            if objects:
                self._create_objects_from_data(scene_id, objects, video_unique_id)
            
            # 2. 이벤트 노드 저장
            events = scene_graph.get('events', [])
            if events:
                self._create_events_from_data(scene_id, events, video_unique_id)
            
            # 3. 공간 관계 저장
            spatial = scene_graph.get('spatial', [])
            if spatial:
                self._create_spatial_from_data(scene_id, spatial, video_unique_id)
            
            # 4. 시간 관계 저장
            temporal = scene_graph.get('temporal', [])
            if temporal:
                self._create_temporal_from_data(scene_id, temporal, video_unique_id)
            
            print(f"✅ 모든 노드 데이터 저장 완료")
            
        except Exception as e:
            print(f"❌ 노드 데이터 저장 실패: {e}")
            raise
    
    def _create_objects_from_data(self, scene_id: int, objects: List[Dict[str, Any]], video_unique_id: int) -> None:
        """객체 노드 데이터 저장"""
        print(f"👥 객체 노드 저장: {len(objects)}개")
        
        for obj in objects:
            try:
                original_object_id = obj.get('object_id')
                new_object_id = f"{video_unique_id}_{scene_id}_object_{original_object_id}"
                
                # label이 없으면 type of를 사용
                label = obj.get('label')
                if not label:
                    label = obj.get('type of', 'unknown')
                
                object_data = {
                    "scene_id": scene_id,
                    "object_id": new_object_id,
                    "super_type": obj.get('super_type', 'unknown'),
                    "type_of": obj.get('type of', 'unknown'),
                    "label": label,
                    "attributes": obj.get('attributes', {})
                }
                
                response = self.session.post(f"{self.db_api_base_url}/objects", json=object_data)
                response.raise_for_status()
                print(f"  ✅ 객체 저장: {obj.get('label')} (ID: {new_object_id})")
                
            except Exception as e:
                print(f"  ❌ 객체 저장 실패: {obj.get('label')} - {e}")
    
    def _create_events_from_data(self, scene_id: int, events: List[Dict[str, Any]], video_unique_id: int) -> None:
        """이벤트 노드 데이터 저장"""
        print(f"🎬 이벤트 노드 저장: {len(events)}개")
        
        for i, event in enumerate(events):
            try:
                original_event_id = event.get('event_id', f"EVT_{i}")
                new_event_id = f"{video_unique_id}_{scene_id}_event_{original_event_id}"
                
                # subject_id와 object_id를 새로운 객체 ID로 매핑
                subject_id = str(event.get('subject', ''))
                object_id = str(event.get('object', '')) if event.get('object') else None
                
                # 객체 ID 매핑 (간단한 매핑 로직)
                if subject_id.isdigit():
                    subject_id = f"{video_unique_id}_{scene_id}_object_{subject_id}"
                if object_id and object_id.isdigit():
                    object_id = f"{video_unique_id}_{scene_id}_object_{object_id}"
                
                event_data = {
                    "scene_id": scene_id,
                    "event_id": new_event_id,
                    "subject_id": subject_id,
                    "verb": event.get('verb', 'unknown_action'),
                    "object_id": object_id,
                    "attributes": {"attribute": event.get('attribute', '')}
                }
                
                response = self.session.post(f"{self.db_api_base_url}/events", json=event_data)
                response.raise_for_status()
                print(f"  ✅ 이벤트 저장: {event.get('verb')} (ID: {new_event_id})")
                
            except Exception as e:
                print(f"  ❌ 이벤트 저장 실패: {event.get('verb')} - {e}")
    
    def _create_spatial_from_data(self, scene_id: int, spatial: List[Dict[str, Any]], video_unique_id: int) -> None:
        """공간 관계 데이터 저장"""
        print(f"📍 공간 관계 저장: {len(spatial)}개")
        
        for i, rel in enumerate(spatial):
            try:
                original_spatial_id = rel.get('spatial_id', f"SPAT_{i}")
                new_spatial_id = f"{video_unique_id}_{scene_id}_spatial_{original_spatial_id}"
                
                # subject_id와 object_id를 새로운 객체 ID로 매핑
                subject_id = str(rel.get('subject', ''))
                object_id = str(rel.get('object', ''))
                
                if subject_id.isdigit():
                    subject_id = f"{video_unique_id}_{scene_id}_object_{subject_id}"
                if object_id.isdigit():
                    object_id = f"{video_unique_id}_{scene_id}_object_{object_id}"
                
                spatial_data = {
                    "scene_id": scene_id,
                    "spatial_id": new_spatial_id,
                    "subject_id": subject_id,
                    "predicate": rel.get('predicate', 'unknown_relation'),
                    "object_id": object_id
                }
                
                response = self.session.post(f"{self.db_api_base_url}/spatial", json=spatial_data)
                response.raise_for_status()
                print(f"  ✅ 공간 관계 저장: {rel.get('predicate')} (ID: {new_spatial_id})")
                
            except Exception as e:
                print(f"  ❌ 공간 관계 저장 실패: {rel.get('predicate')} - {e}")
    
    def _create_temporal_from_data(self, scene_id: int, temporal: List[Dict[str, Any]], video_unique_id: int) -> None:
        """시간 관계 데이터 저장"""
        print(f"⏰ 시간 관계 저장: {len(temporal)}개")
        
        for i, rel in enumerate(temporal):
            try:
                original_temporal_id = rel.get('temporal_id', f"TEMP_{i}")
                new_temporal_id = f"{video_unique_id}_{scene_id}_temporal_{original_temporal_id}"
                
                # subject_id와 object_id를 새로운 이벤트 ID로 매핑
                subject_id = str(rel.get('subject', ''))
                object_id = str(rel.get('object', ''))
                
                if subject_id.isdigit():
                    subject_id = f"{video_unique_id}_{scene_id}_event_{subject_id}"
                if object_id.isdigit():
                    object_id = f"{video_unique_id}_{scene_id}_event_{object_id}"
                
                temporal_data = {
                    "scene_id": scene_id,
                    "temporal_id": new_temporal_id,
                    "subject_id": subject_id,
                    "predicate": rel.get('predicate', 'unknown_relation'),
                    "object_id": object_id
                }
                
                response = self.session.post(f"{self.db_api_base_url}/temporal", json=temporal_data)
                response.raise_for_status()
                print(f"  ✅ 시간 관계 저장: {rel.get('predicate')} (ID: {new_temporal_id})")
                
            except Exception as e:
                print(f"  ❌ 시간 관계 저장 실패: {rel.get('predicate')} - {e}")
    
    def _create_embeddings_from_info(self, scene_id: int, embedding_info: Dict[str, Any], video_unique_id: int) -> None:
        """임베딩 정보에서 임베딩 데이터 저장"""
        print(f"🔗 임베딩 데이터 저장 시작")
        
        try:
            node_info = embedding_info.get('node_info', [])
            node_embeddings = embedding_info.get('node_embeddings', [])
            
            if len(node_info) != len(node_embeddings):
                print(f"❌ 노드 정보와 임베딩 개수가 일치하지 않음: {len(node_info)} vs {len(node_embeddings)}")
                return
            
            # scene 노드는 제외하고 처리
            for i, node in enumerate(node_info):
                node_type = node.get('node_type')
                if node_type == 'scene':
                    continue
                
                original_node_id = node.get('node_id')
                node_label = node.get('node_label', 'unknown')
                
                # 실제 node_id 생성: {video_unique_id}_{scene_id}_{node_type}_{orig_id}
                actual_node_id = f"{video_unique_id}_{scene_id}_{node_type}_{original_node_id}"
                
                # 임베딩 벡터 가져오기
                embedding_vector = node_embeddings[i]
                
                # 임베딩 데이터 저장
                embedding_data = {
                    "node_id": actual_node_id,
                    "node_type": node_type,
                    "embedding": embedding_vector
                }
                
                # 임베딩 저장 API 호출 (직접 데이터베이스에 저장)
                response = self.session.post(f"{self.db_api_base_url}/embeddings", json=embedding_data)
                response.raise_for_status()
                
                print(f"  ✅ 임베딩 저장: {node_label} ({node_type}) - {actual_node_id}")
            
            print(f"✅ 임베딩 데이터 저장 완료: {len([n for n in node_info if n.get('node_type') != 'scene'])}개")
            
        except Exception as e:
            print(f"❌ 임베딩 데이터 저장 실패: {e}")
            raise

    # ==================== 검색 기능 ====================
    
    def vector_search(self, query: str, top_k: int = 5, tau: float = 0.30, use_rgcn: bool = True) -> Dict[str, Any]:
        """
        사용자 질의를 triple로 변환하고 벡터 기반 유사도 검색 수행 (R-GCN 그래프 임베딩 지원)
        
        Args:
            query: 사용자 질의 문자열
            top_k: 반환할 최대 결과 수
            tau: 유사도 임계값
            use_rgcn: R-GCN 그래프 임베딩 사용 여부 (기본값: True)
        
        Returns:
            Dict: 검색 결과 (triples, search_results 포함)
        """
        try:
            print(f"🔍 벡터 검색 시작: '{query}'")
            
            # QueryToTriplesConverter import 및 초기화
            from reference_query_to_triples_converter import QueryToTriplesConverter
            import os
            
            # 1. 질문을 triples로 변환
            converter = QueryToTriplesConverter(
                qa_template_path="templates/qa_to_triple_template.txt",
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini"
            )
            
            triples = converter.convert_question(query)
            if not triples:
                print("❌ 질문을 triple로 변환할 수 없습니다.")
                return {
                    "question": query,
                    "triples": [],
                    "search_results": [],
                    "success": False,
                    "error": "질문을 triple로 변환할 수 없습니다."
                }
            
            print(f"✅ {len(triples)}개 triple 생성 완료")
            
            # 2. DB에서 triple 기반 검색 수행
            search_results = self._search_triples_in_db(triples, tau, top_k, use_rgcn)
            
            print(f"✅ 검색 완료: {len(search_results)}개 결과")
            
            return {
                "question": query,
                "triples": triples,
                "search_results": search_results,
                "success": True,
                "tau": tau,
                "top_k": top_k
            }
            
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {e}")
            return {
                "question": query,
                "triples": [],
                "search_results": [],
                "success": False,
                "error": str(e)
            }
    
    def _search_triples_in_db(self, triples: List[List[str]], tau: float, top_k: int, use_rgcn: bool = True) -> List[Dict[str, Any]]:
        """
        DB에서 triple 기반 벡터 검색 수행 (R-GCN 그래프 임베딩 포함)
        
        Args:
            triples: 검색할 triple 리스트
            tau: 유사도 임계값
            top_k: 반환할 최대 결과 수
            use_rgcn: R-GCN 그래프 임베딩 사용 여부
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            BERT_NAME = "sentence-transformers/all-MiniLM-L6-v2"
            DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
            
            # R-GCN 모델 초기화 (필요한 경우에만)
            rgcn_embedder = None
            if use_rgcn:
                try:
                    from rgcn_model import RGCNEmbedder
                    rgcn_embedder = RGCNEmbedder(
                        model_path="model/embed_triplet_struct_ver1+2/best_model.pt",
                        edge_map_path="config/graph/edge_type_map.json",
                        sbert_model=BERT_NAME,
                        device=DEVICE
                    )
                    print("✅ R-GCN 모델 초기화 완료")
                except Exception as e:
                    print(f"⚠️ R-GCN 모델 초기화 실패, SBERT만 사용: {e}")
                    use_rgcn = False
            
            # SBERT 모델 초기화
            sbert = SentenceTransformer(BERT_NAME, device=DEVICE).eval()
            
            @torch.no_grad()
            def vec(txt: str) -> torch.Tensor:
                return sbert.encode(txt, normalize_embeddings=True, convert_to_tensor=True).float()
            
            def token_to_sentence(tok: str | None) -> str:
                if not tok:
                    return ""
                sup, typ = tok.split(":", 1) if ":" in tok else (tok, tok)
                return f"A {typ} which is a kind of {sup}."
            
            def embed_query_with_rgcn(tokens: List[str]) -> Tuple[torch.Tensor|None, ...]:
                """R-GCN을 사용한 쿼리 임베딩"""
                s_tok, v_tok, o_tok = (tokens + [None, None])[:3]
                try:
                    if rgcn_embedder is None:
                        raise ValueError("R-GCN embedder가 초기화되지 않았습니다.")
                    # R-GCN으로 임베딩
                    q_s, q_v, q_o = rgcn_embedder.embed_triple_with_rgcn(s_tok, v_tok, o_tok)
                    return q_s, q_v, q_o
                except Exception as e:
                    print(f"⚠️ R-GCN 임베딩 실패, SBERT로 fallback: {e}")
                    # Fallback to SBERT
                    q_s = vec(token_to_sentence(s_tok)) if s_tok and s_tok != "None" else None
                    q_v = vec(v_tok) if v_tok and v_tok != "None" else None
                    q_o = (
                        vec(token_to_sentence(o_tok))
                        if o_tok and o_tok not in (None, "", "none", "None") else None
                    )
                    return q_s, q_v, q_o
            
            def embed_query(tokens: List[str]) -> Tuple[torch.Tensor|None, ...]:
                """기존 SBERT 임베딩 (호환성 유지)"""
                s_tok, v_tok, o_tok = (tokens + [None, None])[:3]
                q_s = vec(token_to_sentence(s_tok)) if s_tok and s_tok != "None" else None
                q_v = vec(v_tok) if v_tok and v_tok != "None" else None
                q_o = (
                    vec(token_to_sentence(o_tok))
                    if o_tok and o_tok not in (None, "", "none", "None") else None
                )
                return q_s, q_v, q_o
            
            # 1. triples를 임베딩으로 변환
            print(f"🔍 변환할 triples: {triples}")
            queries_emb = []
            for i, t in enumerate(triples):
                print(f"  Triple {i+1}: {t}")
                try:
                    if use_rgcn:
                        # R-GCN을 사용한 임베딩
                        emb = embed_query_with_rgcn(t)
                        print(f"  R-GCN 임베딩 성공: {[type(e).__name__ if e is not None else 'None' for e in emb]}")
                    else:
                        # SBERT 임베딩
                        emb = embed_query(t)
                        print(f"  SBERT 임베딩 성공: {[type(e).__name__ if e is not None else 'None' for e in emb]}")
                    queries_emb.append(emb)
                except Exception as e:
                    print(f"  ❌ 임베딩 실패: {e}")
                    if use_rgcn:
                        print(f"  ⚠️ R-GCN 실패, SBERT로 fallback 시도...")
                        try:
                            # Fallback to SBERT
                            emb = embed_query(t)
                            print(f"  SBERT fallback 성공: {[type(e).__name__ if e is not None else 'None' for e in emb]}")
                            queries_emb.append(emb)
                        except Exception as e2:
                            print(f"  ❌ SBERT fallback도 실패: {e2}")
                            raise
                    else:
                        raise
            total_q = len(queries_emb)
            
            # 2. DB에서 모든 장면 데이터 조회
            print(f"🔍 DB에서 비디오 목록 조회 중...")
            try:
                videos = self.get_videos()
                print(f"✅ 비디오 {len(videos)}개 조회 완료")
            except Exception as e:
                print(f"❌ 비디오 목록 조회 실패: {e}")
                raise
            heap = []
            
            for video in videos:
                try:
                    print(f"🔍 비디오 {video['id']}의 장면들 조회 중...")
                    scenes = self.get_scenes(video['id'])
                    print(f"✅ 장면 {len(scenes)}개 조회 완료")
                except Exception as e:
                    print(f"❌ 장면 조회 실패 (비디오 {video['id']}): {e}")
                    continue
                
                for scene in scenes:
                    scene_id = scene['id']
                    
                    try:
                        print(f"  🔍 장면 {scene_id}의 노드 데이터 조회 중...")
                        # 장면의 모든 노드 데이터 조회
                        objects = self.get_scene_objects(scene_id)
                        events = self.get_scene_events(scene_id)
                        spatial = self.get_scene_spatial_relations(scene_id)
                        temporal = self.get_scene_temporal_relations(scene_id)
                        embeddings = self.get_scene_embeddings(scene_id)
                        print(f"  ✅ 노드 데이터 조회 완료: 객체 {len(objects)}개, 이벤트 {len(events)}개")
                    except Exception as e:
                        print(f"  ❌ 노드 데이터 조회 실패 (장면 {scene_id}): {e}")
                        continue
                    
                    # 임베딩을 딕셔너리로 변환
                    try:
                        print(f"  🔍 임베딩 데이터 처리 중...")
                        embedding_dict = {}
                        for emb in embeddings:
                            embedding_data = emb['embedding']
                            # 문자열을 파싱해서 텐서로 변환
                            if isinstance(embedding_data, str):
                                # PostgreSQL pgvector 문자열을 파싱 (예: "[0.1,0.2,0.3]")
                                try:
                                    import ast
                                    embedding_list = ast.literal_eval(embedding_data)
                                    embedding_tensor = torch.tensor(embedding_list, dtype=torch.float32)
                                except Exception as e:
                                    print(f"    ❌ 임베딩 파싱 실패: {e}")
                                    continue
                            elif isinstance(embedding_data, list):
                                embedding_tensor = torch.tensor(embedding_data, dtype=torch.float32)
                            else:
                                embedding_tensor = embedding_data
                            embedding_dict[emb['node_id']] = embedding_tensor
                        print(f"  ✅ 임베딩 {len(embedding_dict)}개 처리 완료")
                    except Exception as e:
                        print(f"  ❌ 임베딩 처리 실패: {e}")
                        continue
                    
                    # 장면의 triple 생성 (subject, event, object)
                    try:
                        print(f"  🔍 장면 triple 생성 중...")
                        scene_triples = []
                        for event in events:
                            subject_id = event['subject_id']
                            event_id = event['event_id']
                            object_id = event.get('object_id')
                            verb = event['verb']
                            
                            # 해당 노드들의 임베딩이 있는지 확인
                            if (subject_id in embedding_dict and 
                                event_id in embedding_dict and 
                                (object_id is None or object_id in embedding_dict)):
                                # 임베딩 벡터로 변환
                                subject_emb = embedding_dict[subject_id]
                                event_emb = embedding_dict[event_id]
                                object_emb = embedding_dict.get(object_id) if object_id else None
                                scene_triples.append((subject_emb, event_emb, object_emb, verb))
                        print(f"  ✅ 장면 triple {len(scene_triples)}개 생성 완료")
                    except Exception as e:
                        print(f"  ❌ 장면 triple 생성 실패: {e}")
                        continue
                    
                    if not scene_triples:
                        continue
                    
                    # 3. 각 쿼리에 대해 매칭 수행
                    matched = []
                    used = set()
                    
                    for q_idx, (q_s, q_v, q_o) in enumerate(queries_emb):
                        # 쿼리 임베딩을 같은 디바이스로 이동
                        q_s = q_s.to(DEVICE) if q_s is not None else None
                        q_v = q_v.to(DEVICE) if q_v is not None else None
                        q_o = q_o.to(DEVICE) if q_o is not None else None
                        best = None
                        
                        for subject_emb, event_emb, object_emb, verb in scene_triples:
                            # 객체 필수 여부 판단
                            need_obj = q_o is not None
                            if need_obj and object_emb is None:
                                continue
                            
                            # 임베딩 벡터 가져오기 (이미 텐서이므로 직접 사용)
                            v_s = subject_emb.to(DEVICE)
                            v_v = event_emb.to(DEVICE)
                            v_o = object_emb.to(DEVICE) if object_emb is not None else None
                            
                            # 정규화
                            v_s = F.normalize(v_s.unsqueeze(0), dim=1).squeeze(0)
                            v_v = F.normalize(v_v.unsqueeze(0), dim=1).squeeze(0)
                            if v_o is not None:
                                v_o = F.normalize(v_o.unsqueeze(0), dim=1).squeeze(0)
                            
                            # 유사도 계산
                            s_sim = float(torch.dot(q_s, v_s)) if q_s is not None else None
                            v_sim = float(torch.dot(q_v, v_v)) if q_v is not None else None
                            o_sim = (
                                float(torch.dot(q_o, v_o))
                                if (q_o is not None and v_o is not None) else None
                            )
                            
                            # 임계치 검사
                            if (q_s is not None and s_sim < tau) or \
                               (q_v is not None and v_sim < tau) or \
                               (q_o is not None and o_sim < tau):
                                continue
                            
                            sims = [x for x in (s_sim, v_sim, o_sim) if x is not None]
                            sim = sum(sims) / len(sims)
                            
                            if best is None or sim > best[0]:
                                best = (sim, s_sim, v_sim, o_sim, (subject_id, event_id, object_id))
                        
                        if best:
                            matched.append((q_idx,) + best)
                            used.add(best[-1])
                    
                    if not matched:
                        continue
                    
                    # 결과 저장
                    match_cnt = len(matched)
                    avg_sim = sum(m[1] for m in matched) / match_cnt
                    
                    result = {
                        "scene_id": scene_id,
                        "video_id": video['id'],
                        "drama_name": video['drama_name'],
                        "episode_number": video['episode_number'],
                        "scene_number": scene['scene_number'],
                        "match_count": match_cnt,
                        "avg_similarity": avg_sim,
                        "matched_triples": matched,
                        "total_queries": total_q
                    }
                    
                    heapq.heappush(heap, (match_cnt, avg_sim, result))
                    if len(heap) > top_k:
                        heapq.heappop(heap)
            
            # 결과 정렬 및 반환
            results = sorted(heap, key=lambda x: (-x[0], -x[1]))
            return [result for _, _, result in results]
            
        except Exception as e:
            print(f"❌ DB triple 검색 실패: {e}")
            return []
    
    def print_search_results(self, search_results: List[Dict[str, Any]], triples: List[List[str]]) -> None:
        """
        검색 결과를 출력합니다.
        
        Args:
            search_results: 검색 결과 리스트
            triples: 검색에 사용된 triple 리스트
        """
        if not search_results:
            print("❌ 검색 결과가 없습니다.")
            return
        
        print("\n=== 검색 결과 ===")
        for i, result in enumerate(search_results, 1):
            print(f"\n{i}. 장면: {result['drama_name']} {result['episode_number']} - {result['scene_number']}")
            print(f"   매칭된 triple 수: {result['match_count']}/{result['total_queries']}")
            print(f"   평균 유사도: {result['avg_similarity']:.3f}")
            print(f"   장면 ID: {result['scene_id']}")
            
            # 매칭된 triple 상세 정보 출력
            if result['matched_triples']:
                print("   매칭된 triple 상세:")
                for q_idx, sim, s_sim, v_sim, o_sim, (subj_id, event_id, obj_id) in result['matched_triples']:
                    if q_idx < len(triples):
                        triple_str = " | ".join(str(t) for t in triples[q_idx])
                        print(f"     • Q{q_idx}: {triple_str}")
                        print(f"       유사도: {sim:.3f} (S={s_sim:.3f if s_sim else '--'}, V={v_sim:.3f if v_sim else '--'}, O={o_sim:.3f if o_sim else '--'})")
                        print(f"       매칭된 노드: {subj_id} / {event_id} / {obj_id if obj_id else 'None'}")
    
    def hybrid_search(self, query_text: str, query_embedding: List[float], node_type: str = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (텍스트 + 벡터)
        
        Args:
            query_text: 검색할 텍스트
            query_embedding: 검색할 벡터 (384차원)
            node_type: 노드 타입 필터
            top_k: 반환할 결과 수
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            search_data = {
                "query_text": query_text,
                "query_embedding": query_embedding,
                "node_type": node_type,
                "top_k": top_k
            }
            
            response = self.session.post(f"{self.db_api_base_url}/search/hybrid", json=search_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 하이브리드 검색 실패: {e}")
            return []
    
    # ==================== 데이터 확인 및 관리 ====================
    
    def check_all_data(self) -> None:
        """모든 저장된 데이터 확인"""
        self.checker.check_all_data()
    
    def get_schema_info(self) -> None:
        """데이터베이스 스키마 정보 조회"""
        self.schema_checker.print_schema_summary()
    
    def get_foreign_keys(self) -> List[Dict[str, Any]]:
        """외래키 제약조건 정보 조회"""
        return self.schema_checker.get_foreign_keys()
    
    def get_table_info(self) -> List[Dict[str, Any]]:
        """테이블 기본 정보 조회"""
        return self.schema_checker.get_table_info()
    
    def get_column_info(self, table_name: str = None) -> List[Dict[str, Any]]:
        """컬럼 정보 조회"""
        return self.schema_checker.get_column_info(table_name)
    
    def get_index_info(self) -> List[Dict[str, Any]]:
        """인덱스 정보 조회"""
        return self.schema_checker.get_index_info()
    
    def get_data_summary(self) -> Dict[str, Any]:
        """데이터베이스 요약 정보 조회"""
        try:
            videos = self.get_videos()
            total_scenes = 0
            total_objects = 0
            total_events = 0
            total_embeddings = 0
            
            for video in videos:
                scenes = self.get_scenes(video['id'])
                total_scenes += len(scenes)
                
                for scene in scenes:
                    objects = self.get_scene_objects(scene['id'])
                    events = self.get_scene_events(scene['id'])
                    embeddings = self.get_scene_embeddings(scene['id'])
                    
                    total_objects += len(objects)
                    total_events += len(events)
                    total_embeddings += len(embeddings)
            
            return {
                "total_videos": len(videos),
                "total_scenes": total_scenes,
                "total_objects": total_objects,
                "total_events": total_events,
                "total_embeddings": total_embeddings,
                "videos": videos
            }
        except Exception as e:
            print(f"❌ 데이터 요약 조회 실패: {e}")
            return {}
    
    # ==================== 유틸리티 함수 ====================
    
    def _generate_video_id(self, drama_name: str, episode_number: str) -> int:
        """비디오 고유 ID 생성 (32비트 정수 범위 내)"""
        # 간단한 해시 기반 ID 생성 (32비트 정수 범위 내)
        import hashlib
        content = f"{drama_name}_{episode_number}"
        hash_obj = hashlib.md5(content.encode())
        # 32비트 정수 범위: -2,147,483,648 ~ 2,147,483,647
        # 양수 범위: 0 ~ 2,147,483,647
        return int(hash_obj.hexdigest()[:7], 16) % 2000000000  # 20억 미만으로 제한
    
    def export_scene_data(self, scene_id: int, output_file: str = None) -> bool:
        """
        장면 데이터를 JSON 파일로 내보내기
        
        Args:
            scene_id: 장면 ID
            output_file: 출력 파일 경로 (기본값: scene_{scene_id}.json)
        
        Returns:
            bool: 내보내기 성공 여부
        """
        try:
            scene_data = self.get_scene_graph(scene_id)
            if not scene_data:
                print(f"❌ 장면 {scene_id} 데이터를 찾을 수 없습니다.")
                return False
            
            if output_file is None:
                output_file = f"scene_{scene_id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(scene_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 장면 데이터 내보내기 완료: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 장면 데이터 내보내기 실패: {e}")
            return False
    
    def import_scene_data(self, json_file_path: str) -> bool:
        """
        JSON 파일에서 장면 데이터 가져오기
        
        Args:
            json_file_path: JSON 파일 경로
        
        Returns:
            bool: 가져오기 성공 여부
        """
        return self.upload_scene_graph(json_file_path)
    
    # ==================== 대화형 모드 ====================
    
    def interactive_mode(self) -> None:
        """대화형 모드 실행"""
        print("🎭 장면그래프 데이터베이스 클라이언트")
        print("=" * 50)
        
        while True:
            print("\n사용 가능한 명령어:")
            print("1. 데이터 확인 (check)")
            print("2. 비디오 목록 (list)")
            print("3. 비디오 삭제 (delete)")
            print("4. 장면그래프 업로드 (upload)")
            print("5. 데이터 요약 (summary)")
            print("6. 스키마 정보 (schema)")
            print("7. 종료 (quit)")
            
            choice = input("\n명령어를 선택하세요: ").strip().lower()
            
            if choice == 'check':
                self.check_all_data()
            elif choice == 'list':
                self.list_videos()
            elif choice == 'delete':
                self._interactive_delete()
            elif choice == 'upload':
                self._interactive_upload_new()
            elif choice == 'summary':
                self._show_summary()
            elif choice == 'schema':
                self.get_schema_info()
            elif choice in ['quit', 'exit', 'q']:
                print("👋 프로그램을 종료합니다.")
                break
            else:
                print("❌ 잘못된 명령어입니다.")
    
    def _interactive_delete(self) -> None:
        """대화형 삭제 모드"""
        self.list_videos()
        try:
            video_id = int(input("삭제할 비디오의 고유 ID를 입력하세요: "))
            confirm = input("정말로 삭제하시겠습니까? (yes/no): ").strip().lower() == 'yes'
            self.delete_video(video_id, confirm)
        except ValueError:
            print("❌ 올바른 숫자를 입력해주세요.")
    
    def _interactive_upload_new(self) -> None:
        """대화형 업로드 모드"""
        print("📤 장면그래프 파일 업로드")
        print("JSON 파일과 대응하는 PT 파일을 업로드합니다.")
        
        json_file = input("JSON 파일 경로를 입력하세요: ").strip()
        
        if not json_file:
            print("❌ 파일 경로를 입력해주세요.")
            return
        
        if not os.path.exists(json_file):
            print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
            return
        
        # 파일 업로드 수행
        print(f"\n🚀 업로드 시작: {json_file}")
        success = self.upload_scene_graph(json_file)
        
        if success:
            print(f"✅ 업로드 성공!")
        else:
            print(f"❌ 업로드 실패!")
    
    def search_triples_with_pgvector(self, query_embedding: List[float], node_type: str = "object", top_k: int = 5) -> List[Dict[str, Any]]:
        """
        pgvector를 이용한 Triple 구조 검색 (방법 3)
        
        Args:
            query_embedding: 검색할 벡터 (384차원)
            node_type: 검색할 노드 타입
            top_k: 반환할 최대 결과 수
            
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            print(f"🔍 pgvector Triple 검색 시작...")
            print(f"  - 쿼리 벡터 차원: {len(query_embedding)}")
            print(f"  - 노드 타입: {node_type}")
            print(f"  - 최대 결과: {top_k}개")
            
            # API 요청 데이터 구성
            request_data = {
                "query_embedding": query_embedding,
                "node_type": node_type,
                "top_k": top_k
            }
            
            # API 호출
            response = self.session.post(
                f"{self.db_api_base_url}/search/triple",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ pgvector 검색 완료: {len(results)}개 결과")
                return results
            else:
                print(f"❌ pgvector 검색 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ pgvector 검색 중 오류: {e}")
            return []

    def _show_summary(self) -> None:
        """데이터 요약 표시"""
        summary = self.get_data_summary()
        if summary:
            print("\n📊 데이터베이스 요약:")
            print(f"  - 비디오: {summary['total_videos']}개")
            print(f"  - 장면: {summary['total_scenes']}개")
            print(f"  - 객체: {summary['total_objects']}개")
            print(f"  - 이벤트: {summary['total_events']}개")
            print(f"  - 임베딩: {summary['total_embeddings']}개")


def main():
    """메인 실행 함수"""
    import sys
    
    client = SceneGraphDBClient()
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            client.check_all_data()
        elif command == "list":
            client.list_videos()
        elif command == "summary":
            client._show_summary()
        elif command == "schema":
            client.get_schema_info()
        elif command == "search":
            if len(sys.argv) > 2:
                query = sys.argv[2]
                top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
                tau = float(sys.argv[4]) if len(sys.argv) > 4 else 0.30
                
                print(f"🔍 검색: '{query}' (top_k={top_k}, tau={tau})")
                result = client.vector_search(query, top_k, tau)
                
                if result['success']:
                    print(f"✅ 검색 완료! {len(result['search_results'])}개 결과")
                    client.print_search_results(result['search_results'], result['triples'])
                else:
                    print(f"❌ 검색 실패: {result.get('error', 'Unknown error')}")
            else:
                print("사용법: python scene_graph_client.py search \"질문\" [top_k] [tau]")
        elif command == "upload":
            if len(sys.argv) > 2:
                json_file = sys.argv[2]
                print(f"📤 업로드: {json_file}")
                success = client.upload_scene_graph(json_file)
                
                if success:
                    print(f"✅ 업로드 성공!")
                else:
                    print(f"❌ 업로드 실패!")
            else:
                print("사용법: python scene_graph_client.py upload \"json_file_path\"")
        elif command == "interactive":
            client.interactive_mode()
        else:
            print("사용법:")
            print("  python scene_graph_client.py check        # 데이터 확인")
            print("  python scene_graph_client.py list         # 비디오 목록")
            print("  python scene_graph_client.py summary      # 데이터 요약")
            print("  python scene_graph_client.py schema       # 스키마 정보")
            print("  python scene_graph_client.py upload \"json_file\"  # 파일 업로드")
            print("  python scene_graph_client.py search \"질문\" [top_k] [tau]  # 벡터 검색")
            print("  python scene_graph_client.py interactive  # 대화형 모드")
    else:
        # 기본적으로 대화형 모드 실행
        client.interactive_mode()


if __name__ == "__main__":
    main()
