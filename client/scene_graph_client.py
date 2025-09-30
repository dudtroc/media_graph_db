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
    
    def delete_scene_embeddings(self, scene_id: int) -> bool:
        """특정 장면의 모든 임베딩 정보 삭제 (실제로는 스킵 - 업데이트 로직 활용)"""
        try:
            print(f"🔄 장면 {scene_id}의 임베딩 덮어쓰기 준비")
            
            # 해당 장면의 모든 임베딩 조회
            embeddings = self.get_scene_embeddings(scene_id)
            if not embeddings:
                print(f"⚠️ 장면 {scene_id}에 기존 임베딩이 없습니다.")
                return True
            
            print(f"ℹ️ 장면 {scene_id}에 {len(embeddings)}개의 기존 임베딩이 있습니다.")
            print(f"ℹ️ 새로운 임베딩으로 자동 업데이트됩니다.")
            return True
            
        except Exception as e:
            print(f"❌ 임베딩 확인 실패: {e}")
            return False
    
    # ==================== 장면그래프 업로드 ====================
    
    def upload_scene_graph(self, json_file_path: str, overwrite_embeddings: bool = False) -> bool:
        """
        JSON 파일과 대응하는 PT 파일을 이용하여 장면그래프 데이터를 업로드
        
        Args:
            json_file_path: JSON 파일 경로
            overwrite_embeddings: 기존 임베딩을 덮어쓸지 여부 (기본값: False)
            
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
            
            # 10. 임베딩 덮어쓰기 처리
            if overwrite_embeddings:
                print("🔄 기존 임베딩 덮어쓰기 모드")
                self.delete_scene_embeddings(scene_id)
            
            # 11. 임베딩 데이터 저장
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
    
    def vector_search(self, query: str, top_k: int = 5, tau: float = 0.30) -> Dict[str, Any]:
        """
        사용자 질의를 triple로 변환하고 벡터 기반 유사도 검색 수행 (BERT 임베딩 사용)
        
        Args:
            query: 사용자 질의 문자열
            top_k: 반환할 최대 결과 수
            tau: 유사도 임계값
        
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
            
            # 2. DB에서 triple 기반 검색 수행 (BERT만 사용)
            search_results = self._search_triples_in_db(triples, tau, top_k)
            
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
    
    def _search_triples_in_db(self, triples: List[List[str]], tau: float, top_k: int) -> List[Dict[str, Any]]:
        """
        2단계 pgvector 기반 triple 검색 수행 (BERT 임베딩 사용)
        
        1단계: 우선순위에 따라 노드 검색 (verb > object > subject)
        2단계: 모든 triple 조건을 만족하는 scene 찾기
        
        Args:
            triples: 검색할 triple 리스트
            tau: 유사도 임계값
            top_k: 반환할 최대 결과 수
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            BERT_NAME = "sentence-transformers/all-MiniLM-L6-v2"
            # CUDA 오류 방지를 위해 CPU 강제 사용
            DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
            
            # SBERT 모델 초기화
            sbert = SentenceTransformer(BERT_NAME, device=DEVICE).eval()
            
            @torch.no_grad()
            def vec(txt: str) -> torch.Tensor:
                return sbert.encode(txt, normalize_embeddings=True, convert_to_tensor=True).float()
            
            def token_to_sentence(tok: str | None) -> str:
                """
                토큰을 문장 형태로 변환
                "person:man" -> "A man which is a kind of person."
                """
                if not tok:
                    return ""
                if ":" in tok:
                    super_type, type_of = tok.split(":", 1)
                    return f"A {type_of} which is a kind of {super_type}."
                else:
                    # ":"가 없는 경우 그대로 반환
                    return tok
            
            def embed_query(tokens: List[str]) -> Tuple[torch.Tensor|None, ...]:
                """BERT를 사용한 쿼리 임베딩"""
                s_tok, v_tok, o_tok = (tokens + [None, None])[:3]
                
                # Subject와 Object는 문장 형태로 변환하여 임베딩
                q_s = vec(token_to_sentence(s_tok)) if s_tok and s_tok != "None" else None
                # Predicate는 그대로 임베딩
                q_v = vec(v_tok) if v_tok and v_tok != "None" else None
                # Object는 문장 형태로 변환하여 임베딩
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
                    # BERT 임베딩 사용
                    emb = embed_query(t)
                    print(f"  BERT 임베딩 성공: {[type(e).__name__ if e is not None else 'None' for e in emb]}")
                    queries_emb.append(emb)
                except Exception as e:
                    print(f"  ❌ 임베딩 실패: {e}")
                    raise
            total_q = len(queries_emb)
            
            # 2. 입력 검증
            for i, triple in enumerate(triples):
                if not any(triple):  # 모든 값이 None, "", 또는 False
                    raise ValueError(f"Triple {i+1}의 모든 값이 null입니다: {triple}")
            
            # 3. 모든 triple 조건을 만족하는 scene 찾기
            print(f"🔍 모든 triple 조건을 만족하는 scene 검색 시작...")
            all_scene_results = self._find_scenes_matching_all_triples(queries_emb, triples, tau, top_k)
            
            return all_scene_results
            
        except Exception as e:
            print(f"❌ 2단계 pgvector Triple 검색 실패: {e}")
            return []
    
    def _find_scenes_matching_all_triples(self, queries_emb: List[Tuple], triples: List[List[str]], tau: float, top_k: int) -> List[Dict[str, Any]]:
        """
        모든 triple 조건을 만족하는 scene 찾기
        
        Args:
            queries_emb: 임베딩된 triple 리스트
            triples: 원본 triple 리스트
            tau: 유사도 임계값
            top_k: 반환할 최대 결과 수
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            # 1. 각 triple별로 유사한 노드들 찾기
            all_triple_results = []
            
            for query_idx, (s_emb, v_emb, o_emb) in enumerate(queries_emb):
                print(f"🔍 Triple {query_idx + 1} 검색 중...")
                
                # 1단계: 우선순위에 따라 노드 검색
                similar_nodes = self._find_similar_nodes_by_priority(s_emb, v_emb, o_emb, tau)
                
                print(f"  📊 검색된 노드: Subject {len(similar_nodes['subjects'])}개, Verb {len(similar_nodes['verbs'])}개, Object {len(similar_nodes['objects'])}개")
                
                # 2단계: 해당 triple의 유효한 조합 찾기
                valid_combinations = self._find_valid_combinations_for_triple(
                    similar_nodes, query_idx, triples[query_idx], s_emb, o_emb
                )
                
                print(f"  ✅ 유효한 조합: {len(valid_combinations)}개")
                all_triple_results.append(valid_combinations)
            
            # 2. 모든 triple 조건을 만족하는 scene 찾기
            print(f"🔍 모든 triple 조건을 만족하는 scene 검색...")
            matching_scenes = self._find_scenes_satisfying_all_triples(all_triple_results, triples)
            
            # 3. 결과 정렬 및 상위 k개 선택
            matching_scenes.sort(key=lambda x: x['total_avg_similarity'], reverse=True)
            return matching_scenes[:top_k]
            
        except Exception as e:
            print(f"❌ 모든 triple 조건 검색 실패: {e}")
            return []
    
    def _find_similar_nodes_by_priority(self, s_emb, v_emb, o_emb, tau: float) -> Dict[str, List]:
        """
        우선순위에 따라 유사한 노드들 찾기 (최적화된 버전)
        
        1. predicate가 None이 아닌 경우:
           - Event 노드와 Spatial 노드의 유사도가 높은 것을 탐색
           - 탐색된 predicate를 기준으로 연결된 subject와 object 노드를 DB에서 유사도 계산하여 검색
           - None인 것은 탐색 대상에서 배제하고 아닌 부분을 이용해서 탐색
        
        2. predicate가 None인 경우:
           - subject와 object를 이용해서 탐색 실시
           - None인 것은 탐색 대상에서 배제하고 아닌 부분을 이용해서 탐색
        
        3. subject, predicate, object 모두 None인 경우:
           - 탐색 실시하지 않음
        """
        similar_nodes = {
            'subjects': [],
            'verbs': [],
            'objects': []
        }
        
        # 1. predicate가 None이 아닌 경우
        if v_emb is not None:
            print(f"  🔍 Predicate 기준 검색 시작")
            
            # Event 노드와 Spatial 노드 검색 (전역 검색)
            event_nodes = self._find_similar_nodes_with_pgvector(v_emb, 'event', tau)
            try:
                spatial_nodes = self._find_similar_nodes_with_pgvector(v_emb, 'spatial', tau)
            except Exception as e:
                print(f"  ⚠️ Spatial 노드 검색 실패, Event 노드만 사용: {e}")
                spatial_nodes = []
            
            print(f"  📊 Event 노드: {len(event_nodes)}개, Spatial 노드: {len(spatial_nodes)}개")
            
            # 각 predicate 노드에 대해 연결된 노드들을 DB에서 유사도 계산하여 검색
            for predicate_node in event_nodes + spatial_nodes:
                scene_id = predicate_node.get('scene_id')
                if not scene_id:
                    continue
                
                # 연결된 노드들을 DB에서 유사도 계산하여 검색
                connected_nodes = self._find_connected_nodes_with_similarity(
                    scene_id, predicate_node, s_emb, o_emb, tau
                )
                
                # 결과 추가
                similar_nodes['subjects'].extend(connected_nodes['subjects'])
                similar_nodes['objects'].extend(connected_nodes['objects'])
                similar_nodes['verbs'].append(predicate_node)
        
        # 2. predicate가 None인 경우
        elif s_emb is not None or o_emb is not None:
            print(f"  🔍 Subject/Object 기준 검색 시작")
            
            # Subject가 None이 아닌 경우: 전역 검색
            if s_emb is not None:
                similar_nodes['subjects'] = self._find_similar_nodes_with_pgvector(s_emb, 'object', tau)
                print(f"  📊 Subject 노드: {len(similar_nodes['subjects'])}개")
            
            # Object가 None이 아닌 경우: 전역 검색
            if o_emb is not None:
                similar_nodes['objects'] = self._find_similar_nodes_with_pgvector(o_emb, 'object', tau)
                print(f"  📊 Object 노드: {len(similar_nodes['objects'])}개")
            
            # Subject와 Object가 같은 장면에 있는지 확인
            if s_emb is not None and o_emb is not None:
                valid_subjects = []
                valid_objects = []
                
                for subject in similar_nodes['subjects']:
                    for obj in similar_nodes['objects']:
                        if subject.get('scene_id') == obj.get('scene_id'):
                            valid_subjects.append(subject)
                            valid_objects.append(obj)
                
                similar_nodes['subjects'] = valid_subjects
                similar_nodes['objects'] = valid_objects
                print(f"  ✅ 같은 장면의 Subject-Object 쌍: {len(valid_subjects)}개")
        
        # 3. subject, predicate, object 모두 None인 경우: 검색하지 않음
        else:
            print("  ⚠️ 모든 요소가 None이므로 검색하지 않습니다.")
        
        return similar_nodes
    
    def _find_connected_nodes_with_similarity(self, scene_id: int, predicate_node: Dict[str, Any], 
                                            s_emb: torch.Tensor = None, o_emb: torch.Tensor = None, 
                                            tau: float = 0.1) -> Dict[str, List]:
        """
        장면 내 연결된 노드들을 DB에서 유사도 계산하여 검색
        
        Args:
            scene_id: 장면 ID
            predicate_node: predicate 노드 정보
            s_emb: subject 임베딩
            o_emb: object 임베딩
            tau: 유사도 임계값
            
        Returns:
            연결된 노드들의 딕셔너리
        """
        connected_nodes = {
            'subjects': [],
            'objects': []
        }
        
        try:
            # Event 노드인 경우
            if 'event_id' in predicate_node:
                subject_id = predicate_node.get('subject_id')
                object_id = predicate_node.get('object_id')
                
                print(f"  🔍 Event {predicate_node.get('event_id')} 매칭 시도:")
                print(f"    - Subject ID: {subject_id}")
                print(f"    - Object ID: {object_id}")
                
                # Subject 노드 유사도 검색 (DB에서 계산)
                if s_emb is not None and subject_id:
                    # 장면 내에서 유사한 Subject 검색 (specific_node_id 없이)
                    # Subject 검색은 더 관대한 임계값 사용 (tau의 50%)
                    subject_tau = max(0.0, tau * 0.5)
                    subject_results = self._search_similarity_in_db(
                        s_emb, 'object', subject_tau, 
                        scene_id=scene_id
                    )
                    # 검색된 Subject 중에서 Event의 subject_id와 일치하는 것만 필터링
                    matching_subjects = [s for s in subject_results if s['object_id'] == subject_id]
                    connected_nodes['subjects'].extend(matching_subjects)
                    print(f"  📊 Subject 검색 결과: {len(subject_results)}개 (장면 내)")
                    print(f"    - 매칭된 Subject: {len(matching_subjects)}개")
                    if matching_subjects:
                        print(f"    - 찾은 Subject: {[s['object_id'] for s in matching_subjects]}")
                    else:
                        print(f"    - Subject 매칭 실패: {subject_id}")
                
                # Object 노드 유사도 검색 (DB에서 계산)
                if object_id:
                    # o_emb가 None이어도 object 검색 수행 (기본 임베딩 사용)
                    if o_emb is not None:
                        # 장면 내에서 유사한 Object 검색 (specific_node_id 없이)
                        # Object 검색은 더 관대한 임계값 사용 (tau의 50%)
                        object_tau = max(0.0, tau * 0.5)
                        object_results = self._search_similarity_in_db(
                            o_emb, 'object', object_tau,
                            scene_id=scene_id
                        )
                        # 검색된 Object 중에서 Event의 object_id와 일치하는 것만 필터링
                        matching_objects = [o for o in object_results if o['object_id'] == object_id]
                        connected_nodes['objects'].extend(matching_objects)
                        print(f"  📊 Object 검색 결과: {len(object_results)}개 (장면 내)")
                        print(f"    - 매칭된 Object: {len(matching_objects)}개")
                        if matching_objects:
                            print(f"    - 찾은 Object: {[o['object_id'] for o in matching_objects]}")
                        else:
                            print(f"    - Object 매칭 실패: {object_id}")
                    else:
                        # o_emb가 None인 경우, object_id만으로 검색 (유사도 계산 없이)
                        # 장면 내에서 해당 object_id를 가진 객체를 찾기
                        object_results = self._search_similarity_in_db(
                            None, 'object', 0.0,  # 유사도 계산 없이
                            scene_id=scene_id, specific_node_id=object_id
                        )
                        if object_results:
                            connected_nodes['objects'].extend(object_results)
                            print(f"  📊 Object 검색 결과: {len(object_results)}개 (장면 내)")
                            print(f"    - 찾은 Object: {[o['object_id'] for o in object_results]}")
                        else:
                            print(f"    - Object 매칭 실패: {object_id}")
            
            # Spatial 노드인 경우
            elif 'spatial_id' in predicate_node:
                subject_id = predicate_node.get('subject_id')
                object_id = predicate_node.get('object_id')
                
                print(f"  🔍 Spatial {predicate_node.get('spatial_id')} 매칭 시도:")
                print(f"    - Subject ID: {subject_id}")
                print(f"    - Object ID: {object_id}")
                
                # Subject 노드 유사도 검색 (DB에서 계산)
                if s_emb is not None and subject_id:
                    # 장면 내에서 유사한 Subject 검색 (specific_node_id 없이)
                    subject_tau = max(0.0, tau * 0.5)  # Subject 검색을 위한 더 관대한 임계값
                    subject_results = self._search_similarity_in_db(
                        s_emb, 'object', subject_tau,
                        scene_id=scene_id
                    )
                    # 검색된 Subject 중에서 Spatial의 subject_id와 일치하는 것만 필터링
                    matching_subjects = [s for s in subject_results if s['object_id'] == subject_id]
                    connected_nodes['subjects'].extend(matching_subjects)
                    print(f"  📊 Subject 검색 결과: {len(subject_results)}개 (장면 내)")
                    print(f"    - 매칭된 Subject: {len(matching_subjects)}개")
                    if matching_subjects:
                        print(f"    - 찾은 Subject: {[s['object_id'] for s in matching_subjects]}")
                    else:
                        print(f"    - Subject 매칭 실패: {subject_id}")
                
                # Object 노드 유사도 검색 (DB에서 계산)
                if object_id:
                    # o_emb가 None이어도 object 검색 수행 (기본 임베딩 사용)
                    if o_emb is not None:
                        # 장면 내에서 유사한 Object 검색 (specific_node_id 없이)
                        object_tau = max(0.0, tau * 0.5)  # Object 검색을 위한 더 관대한 임계값
                        object_results = self._search_similarity_in_db(
                            o_emb, 'object', object_tau,
                            scene_id=scene_id
                        )
                        # 검색된 Object 중에서 Spatial의 object_id와 일치하는 것만 필터링
                        matching_objects = [o for o in object_results if o['object_id'] == object_id]
                        connected_nodes['objects'].extend(matching_objects)
                        print(f"  📊 Object 검색 결과: {len(object_results)}개 (장면 내)")
                        print(f"    - 매칭된 Object: {len(matching_objects)}개")
                        if matching_objects:
                            print(f"    - 찾은 Object: {[o['object_id'] for o in matching_objects]}")
                        else:
                            print(f"    - Object 매칭 실패: {object_id}")
                    else:
                        # o_emb가 None인 경우, object_id만으로 검색 (유사도 계산 없이)
                        # 장면 내에서 해당 object_id를 가진 객체를 찾기
                        object_results = self._search_similarity_in_db(
                            None, 'object', 0.0,  # 유사도 계산 없이
                            scene_id=scene_id, specific_node_id=object_id
                        )
                        if object_results:
                            connected_nodes['objects'].extend(object_results)
                            print(f"  📊 Object 검색 결과: {len(object_results)}개 (장면 내)")
                            print(f"    - 찾은 Object: {[o['object_id'] for o in object_results]}")
                        else:
                            print(f"    - Object 매칭 실패: {object_id}")
            
            print(f"  📊 연결된 노드: Subject {len(connected_nodes['subjects'])}개, Object {len(connected_nodes['objects'])}개")
            
        except Exception as e:
            print(f"❌ 연결된 노드 검색 실패: {e}")
        
        return connected_nodes

    def _search_similarity_in_db(self, query_emb: torch.Tensor, node_type: str, tau: float, 
                               scene_id: int = None, specific_node_id: str = None) -> List[Dict[str, Any]]:
        """
        DB에서 유사도 계산하여 검색 (서버에서 pgvector 사용)
        
        Args:
            query_emb: 쿼리 임베딩
            node_type: 노드 타입
            tau: 유사도 임계값
            scene_id: 장면 ID (선택사항)
            specific_node_id: 특정 노드 ID (선택사항)
            
        Returns:
            검색 결과 리스트
        """
        if query_emb is None:
            # query_emb가 None인 경우, specific_node_id만으로 검색
            if specific_node_id is None:
                return []
            # specific_node_id가 있는 경우, 해당 노드를 직접 조회
            # 이 경우 유사도 계산 없이 정확한 매칭만 수행
            request_data = {
                "node_type": node_type,
                "specific_node_id": specific_node_id
            }
            if scene_id is not None:
                request_data["scene_id"] = scene_id
            
            try:
                response = self.session.post(f"{self.db_api_base_url}/search/vector", json=request_data)
                response.raise_for_status()
                result = response.json()
                # 서버가 직접 리스트를 반환하는 경우와 {'results': [...]} 형태를 반환하는 경우 모두 처리
                if isinstance(result, list):
                    return result
                else:
                    return result.get('results', [])
            except Exception as e:
                print(f"❌ specific_node_id 검색 실패: {e}")
                return []
        
        # 벡터를 리스트로 변환
        query_vector = query_emb.tolist()
        
        # API 요청 데이터 구성
        request_data = {
            "query_embedding": query_vector,
            "node_type": node_type,
            "tau": tau,
            "top_k": 10
        }
        
        # 선택적 파라미터 추가
        if scene_id is not None:
            request_data["scene_id"] = scene_id
        if specific_node_id is not None:
            request_data["specific_node_id"] = specific_node_id
        
        try:
            # API 호출 (서버에서 pgvector로 유사도 계산)
            response = self.session.post(
                f"{self.db_api_base_url}/search/vector",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                return results
            else:
                print(f"❌ {node_type} 노드 검색 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ {node_type} 노드 검색 중 오류: {e}")
            return []

    def _find_node_by_id(self, node_id: str, node_type: str, scene_id: int) -> Dict[str, Any]:
        """
        특정 ID로 노드 검색
        
        Args:
            node_id: 노드 ID
            node_type: 노드 타입 ('object', 'event', 'spatial')
            scene_id: 장면 ID
            
        Returns:
            노드 정보 딕셔너리 또는 None
        """
        try:
            print(f"🔍 노드 검색: node_id={node_id}, node_type={node_type}, scene_id={scene_id}")
            
            # API를 통해 특정 노드 검색
            if node_type == 'object':
                response = self.session.get(f"{self.db_api_base_url}/objects")
            elif node_type == 'event':
                response = self.session.get(f"{self.db_api_base_url}/events")
            elif node_type == 'spatial':
                response = self.session.get(f"{self.db_api_base_url}/spatial")
            else:
                return None
            
            if response.status_code == 200:
                nodes = response.json()
                print(f"📊 {node_type} 노드 개수: {len(nodes)}")
                
                for node in nodes:
                    node_key = 'object_id' if node_type == 'object' else 'event_id' if node_type == 'event' else 'spatial_id'
                    if node.get(node_key) == node_id:
                        if node.get('scene_id') == scene_id:
                            print(f"✅ 노드 찾음: {node_id}")
                            return node
                        else:
                            print(f"⚠️ 노드는 있지만 다른 장면: {node_id} (scene_id: {node.get('scene_id')})")
                
                print(f"❌ 노드를 찾을 수 없음: {node_id}")
                return None
            else:
                print(f"❌ 노드 검색 API 호출 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 노드 검색 실패: {e}")
            return None
    
    
    def _find_valid_combinations_for_triple(self, similar_nodes: Dict[str, List], query_idx: int, triple: List[str], s_emb: torch.Tensor = None, o_emb: torch.Tensor = None) -> List[Dict[str, Any]]:
        """
        특정 triple에 대한 유효한 조합 찾기
        이미 predicate 기준으로 찾았으므로 단순히 결과를 반환
        """
        valid_combinations = []
        
        # Predicate가 있는 경우: 이미 매칭된 결과들을 조합
        if similar_nodes['verbs']:
            # Event 노드들 처리
            for verb_node in similar_nodes['verbs']:
                if 'event_id' in verb_node:
                    # 해당 event와 매칭되는 subject, object 찾기
                    subject_match = None
                    object_match = None
                    
                    print(f"    🔍 Event {verb_node.get('event_id')} 매칭 시도:")
                    print(f"      - Subject ID: {verb_node.get('subject_id')}")
                    print(f"      - Object ID: {verb_node.get('object_id')}")
                    print(f"      - Available subjects: {[s['object_id'] for s in similar_nodes['subjects']]}")
                    print(f"      - Available objects: {[o['object_id'] for o in similar_nodes['objects']]}")
                    
                    for subject in similar_nodes['subjects']:
                        if subject['object_id'] == verb_node.get('subject_id'):
                            subject_match = subject
                            print(f"      ✅ Subject 매칭 성공: {subject['object_id']} (유사도: {subject['similarity']:.3f})")
                            break
                    
                    # Subject 매칭이 실패한 경우 디버깅 정보 출력
                    if not subject_match:
                        print(f"      ❌ Subject 매칭 실패: {verb_node.get('subject_id')}")
                        print(f"        - Available subjects: {[s['object_id'] for s in similar_nodes['subjects']]}")
                    
                    for obj in similar_nodes['objects']:
                        if obj['object_id'] == verb_node.get('object_id'):
                            object_match = obj
                            print(f"      ✅ Object 매칭 성공: {obj['object_id']} (유사도: {obj['similarity']:.3f})")
                            break
                    
                    # Subject가 매칭되어야만 결과 생성 (Subject 매칭이 실패한 경우는 제외)
                    if subject_match and (object_match or not verb_node.get('object_id')):
                        # 유사도 계산
                        subject_sim = subject_match['similarity'] if subject_match else 0.0
                        verb_sim = verb_node['similarity']
                        object_sim = object_match['similarity'] if object_match else 0.0
                        
                        # 평균 유사도 계산
                        if subject_match and object_match and verb_node.get('object_id'):
                            avg_similarity = (subject_sim + verb_sim + object_sim) / 3
                        elif subject_match:
                            avg_similarity = (subject_sim + verb_sim) / 2
                        else:
                            # Subject가 None인 경우 Predicate만으로 계산
                            avg_similarity = verb_sim
                        
                        valid_combinations.append({
                            "query_idx": query_idx,
                            "subject_id": verb_node.get('subject_id'),
                            "subject_similarity": subject_sim,
                            "subject_info": subject_match,
                            "event_id": verb_node['event_id'],
                            "event_similarity": verb_sim,
                            "object_id": verb_node.get('object_id'),
                            "object_similarity": object_sim if verb_node.get('object_id') and object_match else None,
                            "object_info": object_match,
                            "verb": verb_node['verb'],
                            "avg_similarity": avg_similarity,
                            "scene_id": verb_node['scene_id'],
                            "scene_number": verb_node['scene_number'],
                            "drama_name": verb_node.get('drama_name', 'Unknown'),
                            "episode_number": verb_node.get('episode_number', 'Unknown'),
                            "video_unique_id": verb_node.get('video_unique_id', 0),
                            "type": "event_triple"
                        })
            
            # Spatial 노드들 처리
            for verb_node in similar_nodes['verbs']:
                if 'spatial_id' in verb_node:
                    # 해당 spatial과 매칭되는 subject, object 찾기
                    subject_match = None
                    object_match = None
                    
                    for subject in similar_nodes['subjects']:
                        if subject['object_id'] == verb_node.get('subject_id'):
                            subject_match = subject
                            break
                    
                    for obj in similar_nodes['objects']:
                        if obj['object_id'] == verb_node.get('object_id'):
                            object_match = obj
                            break
                    
                    # Subject가 매칭되어야만 결과 생성 (Subject 매칭이 실패한 경우는 제외)
                    if subject_match and object_match:
                        # 유사도 계산
                        subject_sim = subject_match['similarity'] if subject_match else 0.0
                        predicate_sim = verb_node['similarity']
                        object_sim = object_match['similarity'] if object_match else 0.0
                        
                        # 평균 유사도 계산
                        if subject_match and object_match:
                            avg_similarity = (subject_sim + predicate_sim + object_sim) / 3
                        else:
                            # Subject가 None인 경우 Predicate만으로 계산
                            avg_similarity = predicate_sim
                        
                        valid_combinations.append({
                            "query_idx": query_idx,
                            "subject_id": verb_node.get('subject_id'),
                            "subject_similarity": subject_sim,
                            "subject_info": subject_match,
                            "spatial_id": verb_node['spatial_id'],
                            "predicate_similarity": predicate_sim,
                            "object_id": verb_node.get('object_id'),
                            "object_similarity": object_sim,
                            "object_info": object_match,
                            "predicate": verb_node['predicate'],
                            "avg_similarity": avg_similarity,
                            "scene_id": verb_node['scene_id'],
                            "scene_number": verb_node['scene_number'],
                            "drama_name": verb_node.get('drama_name', 'Unknown'),
                            "episode_number": verb_node.get('episode_number', 'Unknown'),
                            "video_unique_id": verb_node.get('video_unique_id', 0),
                            "type": "spatial_triple"
                        })
        
        # Predicate가 None인 경우: subject와 object만으로 매칭
        else:
            for subject in similar_nodes['subjects']:
                for obj in similar_nodes['objects']:
                    # 같은 장면에 있는지 확인
                    if subject.get('scene_id') == obj.get('scene_id'):
                        # 유사도 계산
                        subject_sim = subject['similarity']
                        object_sim = obj['similarity']
                        avg_similarity = (subject_sim + object_sim) / 2
                        
                        valid_combinations.append({
                            "query_idx": query_idx,
                            "subject_id": subject['object_id'],
                            "subject_similarity": subject_sim,
                            "object_id": obj['object_id'],
                            "object_similarity": object_sim,
                            "avg_similarity": avg_similarity,
                            "scene_id": subject['scene_id'],
                            "scene_number": subject['scene_number'],
                            "drama_name": subject.get('drama_name', 'Unknown'),
                            "episode_number": subject.get('episode_number', 'Unknown'),
                            "video_unique_id": subject.get('video_unique_id', 0),
                            "type": "subject_object_only"
                        })
        
        return valid_combinations
    
    def _find_scenes_satisfying_all_triples(self, all_triple_results: List[List[Dict]], triples: List[List[str]]) -> List[Dict[str, Any]]:
        """
        모든 triple 조건을 만족하는 scene 찾기
        """
        if not all_triple_results:
            return []
        
        # 첫 번째 triple의 결과를 기준으로 시작
        base_results = all_triple_results[0]
        matching_scenes = []
        
        for base_result in base_results:
            scene_id = base_result['scene_id']
            video_id = base_result.get('video_unique_id')
            
            # 이 scene이 모든 triple 조건을 만족하는지 확인
            satisfied_triples = [base_result]
            
            for triple_idx in range(1, len(all_triple_results)):
                triple_results = all_triple_results[triple_idx]
                
                # 같은 scene에서 이 triple의 조건을 만족하는 결과가 있는지 확인
                matching_result = None
                for result in triple_results:
                    if result['scene_id'] == scene_id:
                        matching_result = result
                        break
                
                if matching_result:
                    satisfied_triples.append(matching_result)
                else:
                    # 이 scene은 모든 조건을 만족하지 않음
                    break
            
            # 모든 triple 조건을 만족하는 경우
            if len(satisfied_triples) == len(triples):
                # 전체 유사도 계산
                total_avg_similarity = sum(t['avg_similarity'] for t in satisfied_triples) / len(satisfied_triples)
                
                matching_scenes.append({
                    "scene_id": scene_id,
                    "scene_number": base_result['scene_number'],
                    "drama_name": base_result['drama_name'],
                    "episode_number": base_result['episode_number'],
                    "video_unique_id": base_result['video_unique_id'],
                    "total_avg_similarity": total_avg_similarity,
                    "satisfied_triples": satisfied_triples,
                    "triple_count": len(satisfied_triples),
                    "total_triples": len(triples)
                })
        
        return matching_scenes
    
    def _find_similar_nodes_with_pgvector(self, query_emb: torch.Tensor, node_type: str, tau: float, top_k: int = 100) -> List[Dict[str, Any]]:
        """pgvector로 유사한 노드들 찾기"""
        if query_emb is None:
            return []
        
        # 벡터를 리스트로 변환
        query_vector = query_emb.tolist()
        
        # API 요청 데이터 구성
        request_data = {
            "query_embedding": query_vector,
            "node_type": node_type,
            "tau": tau,
            "top_k": 100
        }
        
        try:
            # API 호출
            response = self.session.post(
                f"{self.db_api_base_url}/search/vector",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                return results
            else:
                print(f"❌ {node_type} 노드 검색 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ {node_type} 노드 검색 중 오류: {e}")
            return []
    
    def _find_related_triples_with_pgvector(self, subjects: List[Dict], verbs: List[Dict], 
                                          objects: List[Dict], query_idx: int) -> List[Dict[str, Any]]:
        """실제 관계를 가지는 Triple 조합 찾기"""
        if not subjects or not verbs:
            return []
        
        # 노드 ID 리스트 추출 (API 응답 구조에 맞게 수정)
        subject_ids = [s['object_id'] for s in subjects]
        verb_ids = [v['event_id'] for v in verbs]
        object_ids = [o['object_id'] for o in objects] if objects else []
        
        # 유사도 매핑 딕셔너리 생성
        subject_sim_map = {s['object_id']: s['similarity'] for s in subjects}
        verb_sim_map = {v['event_id']: v['similarity'] for v in verbs}
        object_sim_map = {o['object_id']: o['similarity'] for o in objects}
        
        # 관계 확인을 위한 API 요청
        try:
            valid_triples = []
            
            # 비디오별로 그룹화하여 같은 비디오 내에서 관계 찾기
            video_groups = {}
            
            # Subject들을 비디오별로 그룹화
            for subject in subjects:
                video_id = subject.get('video_id')
                if video_id not in video_groups:
                    video_groups[video_id] = {'subjects': [], 'verbs': [], 'objects': []}
                video_groups[video_id]['subjects'].append(subject)
            
            # Verb들을 비디오별로 그룹화
            for verb in verbs:
                video_id = verb.get('video_id')
                if video_id not in video_groups:
                    video_groups[video_id] = {'subjects': [], 'verbs': [], 'objects': []}
                video_groups[video_id]['verbs'].append(verb)
            
            # Object들을 비디오별로 그룹화
            for obj in objects:
                video_id = obj.get('video_id')
                if video_id not in video_groups:
                    video_groups[video_id] = {'subjects': [], 'verbs': [], 'objects': []}
                video_groups[video_id]['objects'].append(obj)
            
            # 각 비디오별로 관계 확인
            for video_id, groups in video_groups.items():
                if not groups['subjects'] or not groups['verbs']:
                    continue
                
                # 해당 비디오의 모든 장면에서 이벤트 확인
                scenes = self.get_scenes(video_id)
                
                for scene in scenes:
                    scene_id = scene['id']
                    events = self.get_scene_events(scene_id)
                    
                    for event in events:
                        event_id = event['event_id']
                        subject_id = event['subject_id']
                        object_id = event.get('object_id')
                        verb = event['verb']
                        
                        # Subject와 Verb가 모두 검색 결과에 있는지 확인
                        subject_match = None
                        verb_match = None
                        object_match = None
                        
                        # Subject 매칭
                        for s in groups['subjects']:
                            if s['object_id'] == subject_id:
                                subject_match = s
                                break
                        
                        # Verb 매칭
                        for v in groups['verbs']:
                            if v['event_id'] == event_id:
                                verb_match = v
                                break
                        
                        # Object 매칭 (있는 경우)
                        if object_id and groups['objects']:
                            for o in groups['objects']:
                                if o['object_id'] == object_id:
                                    object_match = o
                                    break
                        elif not object_id and not groups['objects']:
                            # Object가 없고 검색 결과에도 없는 경우 (정상)
                            object_match = True
                        
                        # 모든 요소가 매칭되면 유효한 Triple
                        if subject_match and verb_match and (object_match or object_match is True):
                            subject_sim = subject_match['similarity']
                            verb_sim = verb_match['similarity']
                            object_sim = object_match['similarity'] if object_match and object_match is not True else 0.0
                            
                            # 평균 유사도 계산
                            if object_id and object_match and object_match is not True:
                                avg_similarity = (subject_sim + verb_sim + object_sim) / 3
                            else:
                                avg_similarity = (subject_sim + verb_sim) / 2
                            
                            valid_triples.append({
                                "query_idx": query_idx,
                                "subject_id": subject_id,
                                "subject_similarity": subject_sim,
                                "event_id": event_id,
                                "event_similarity": verb_sim,
                                "object_id": object_id,
                                "object_similarity": object_sim if object_id and object_match and object_match is not True else None,
                                "verb": verb,
                                "avg_similarity": avg_similarity,
                                "scene_id": scene_id,
                                "scene_number": scene['scene_number'],
                                "drama_name": subject_match.get('drama_name', 'Unknown'),
                                "episode_number": subject_match.get('episode_number', 'Unknown'),
                                "video_unique_id": subject_match.get('video_unique_id', 0)
                            })
            
            return valid_triples
            
        except Exception as e:
            print(f"❌ 관계 확인 실패: {e}")
            return []
    
    def _find_similar_nodes_in_scene(self, query_emb: torch.Tensor, node_type: str, scene_id: int, tau: float) -> List[Dict[str, Any]]:
        """특정 장면에서 유사한 노드들 찾기"""
        if query_emb is None:
            return []
        
        # 벡터를 리스트로 변환
        query_vector = query_emb.tolist()
        
        # API 요청 데이터 구성
        request_data = {
            "query_embedding": query_vector,
            "node_type": node_type,
            "tau": tau,
            "top_k": 50,
            "scene_id": scene_id  # 특정 장면으로 제한
        }
        
        try:
            # API 호출
            response = self.session.post(
                f"{self.db_api_base_url}/search/vector",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                return results
            else:
                print(f"❌ 장면 내 벡터 검색 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 장면 내 벡터 검색 API 호출 실패: {e}")
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
            print(f"   전체 평균 유사도: {result['total_avg_similarity']:.3f}")
            print(f"   장면 ID: {result['scene_id']}")
            print(f"   매칭된 Triple: {result['triple_count']}/{result['total_triples']}개")
            
            # 각 Triple별 상세 정보 출력
            if 'satisfied_triples' in result:
                print("   매칭된 Triple 상세:")
                for j, triple_result in enumerate(result['satisfied_triples']):
                    q_idx = triple_result['query_idx']
                    if q_idx < len(triples):
                        triple_str = " | ".join(str(t) for t in triples[q_idx])
                        print(f"     • Triple {j+1}: {triple_str}")
                        print(f"       유사도: {triple_result['avg_similarity']:.3f}")
                        # Subject 정보 출력
                        subject_info = triple_result.get('subject_info')
                        if subject_info:
                            subject_type = subject_info.get('type_of', 'Unknown')
                            subject_super = subject_info.get('super_type', 'Unknown')
                            print(f"       Subject: {triple_result['subject_id']} - {subject_type} ({subject_super}) (유사도: {triple_result['subject_similarity']:.3f})")
                        else:
                            # Subject 매칭이 실패한 경우, Event의 subject_id만 표시
                            print(f"       Subject: {triple_result['subject_id']} (유사도: {triple_result['subject_similarity']:.3f}) - 매칭 실패")
                        
                        # Event 노드인 경우
                        if 'event_id' in triple_result:
                            print(f"       Verb: {triple_result['event_id']} - {triple_result['verb']} (유사도: {triple_result['event_similarity']:.3f})")
                        # Spatial 노드인 경우
                        elif 'spatial_id' in triple_result:
                            print(f"       Predicate: {triple_result['spatial_id']} - {triple_result['predicate']} (유사도: {triple_result['predicate_similarity']:.3f})")
                        # Subject-Object만 있는 경우
                        elif triple_result.get('type') == 'subject_object_only':
                            print(f"       Type: Subject-Object 매칭 (Predicate 없음)")
                        
                        if triple_result['object_id']:
                            obj_sim = triple_result.get('object_similarity')
                            object_info = triple_result.get('object_info')
                            if object_info:
                                object_type = object_info.get('type_of', 'Unknown')
                                object_super = object_info.get('super_type', 'Unknown')
                                if obj_sim is not None:
                                    print(f"       Object: {triple_result['object_id']} - {object_type} ({object_super}) (유사도: {obj_sim:.3f})")
                                else:
                                    print(f"       Object: {triple_result['object_id']} - {object_type} ({object_super}) (유사도: N/A)")
                            else:
                                if obj_sim is not None:
                                    print(f"       Object: {triple_result['object_id']} (유사도: {obj_sim:.3f})")
                                else:
                                    print(f"       Object: {triple_result['object_id']} (유사도: N/A)")
                        else:
                            print(f"       Object: None")
            else:
                # 기존 형식 지원 (하위 호환성)
                print(f"   평균 유사도: {result.get('avg_similarity', 0):.3f}")
                if 'subject_id' in result:
                    print(f"   Subject: {result['subject_id']}")
                    print(f"   Verb: {result['event_id']} - {result['verb']}")
                    if result.get('object_id'):
                        print(f"   Object: {result['object_id']}")
    
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
