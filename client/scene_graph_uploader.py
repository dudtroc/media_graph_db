#!/usr/bin/env python3
"""
장면 그래프 데이터 업로더
JSON 파일에서 장면 그래프 데이터를 읽어와서 DB에 저장
"""

import json
import os
import re
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class SceneGraphUploader:
    """장면 그래프 데이터 업로더 클래스"""
    
    def __init__(self, api_base_url: str = None):
        """초기화"""
        self.api_base_url = api_base_url or os.getenv("API_URL", "http://localhost:8000")
        print(f"🌐 API 서버: {self.api_base_url}")
    
    def parse_filename(self, filename: str) -> Dict[str, str]:
        """
        파일명에서 VIDEO와 SCENES 정보 추출
        
        예시: "Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json"
        """
        print(f"📁 파일명 파싱: {filename}")
        
        # 파일명에서 정보 추출
        match = re.match(r'(.+)_(.+)_visual_(\d+)-(\d+)_.*_meta_info\.json', filename)
        if not match:
            raise ValueError(f"파일명 형식이 올바르지 않습니다: {filename}")
        
        drama_name, episode_number, start_frame, end_frame = match.groups()
        
        # EP01 -> EP01로 유지
        if episode_number.startswith('EP'):
            episode_number = episode_number
        
        result = {
            'drama_name': drama_name,
            'episode_number': episode_number,
            'start_frame': int(start_frame),
            'end_frame': int(end_frame)
        }
        
        print(f"✅ 파싱 결과: {result}")
        return result
    
    def load_scene_graph_data(self, file_path: str) -> Dict[str, Any]:
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
    
    def check_existing_video(self, drama_name: str, episode_number: str) -> Optional[Dict[str, Any]]:
        """기존 비디오 데이터 확인"""
        print(f"🔍 기존 비디오 확인: {drama_name} {episode_number}")
        
        try:
            response = requests.get(f"{self.api_base_url}/videos")
            if response.status_code == 200:
                videos = response.json()
                for video in videos:
                    if (video.get('drama_name') == drama_name and 
                        video.get('episode_number') == episode_number):
                        print(f"✅ 기존 비디오 발견: ID {video.get('id')}")
                        return video
            print("ℹ️  기존 비디오 없음")
            return None
        except Exception as e:
            print(f"⚠️  비디오 확인 중 오류: {e}")
            return None
    
    def create_video(self, drama_name: str, episode_number: str) -> Optional[int]:
        """새 비디오 생성"""
        print(f"🆕 새 비디오 생성: {drama_name} {episode_number}")
        
        try:
            # video_unique_id 생성
            video_unique_id = self._generate_video_id(drama_name, episode_number)
            
            video_data = {
                "video_unique_id": video_unique_id,
                "drama_name": drama_name,
                "episode_number": episode_number
            }
            
            response = requests.post(f"{self.api_base_url}/videos", json=video_data)
            if response.status_code == 200:
                result = response.json()
                video_id = result.get('video_id')
                print(f"✅ 새 비디오 생성 성공: ID {video_id}")
                return video_id
            else:
                print(f"❌ 비디오 생성 실패: {response.text}")
                return None
        except Exception as e:
            print(f"❌ 비디오 생성 오류: {e}")
            return None
    
    def create_or_update_video(self, drama_name: str, episode_number: str) -> Optional[int]:
        """비디오 생성 또는 기존 것 반환"""
        print(f"🎬 비디오 생성/확인: {drama_name} {episode_number}")
        
        # 기존 비디오 확인 (한 번만)
        existing_video = self.check_existing_video(drama_name, episode_number)
        
        if existing_video:
            print(f"✅ 기존 비디오 사용: ID {existing_video.get('id')}")
            return existing_video.get('id')
        
        # 새 비디오 생성
        print(f"🆕 새 비디오 생성")
        return self.create_video(drama_name, episode_number)
    
    def create_scene(self, video_id: int, scene_data: Dict[str, Any], 
                     start_frame: int, end_frame: int, pt_file_path: str = None) -> Optional[int]:
        """장면 데이터 생성 (임베딩 포함)"""
        print(f"🎭 장면 생성: 프레임 {start_frame}-{end_frame}")
        
        # 장면 메타데이터 준비
        scene_meta = scene_data.get('scene_graph', {}).get('meta', {})
        
        # video_id를 video_unique_id로 변환
        video_unique_id = self._get_video_unique_id_from_id(video_id)
        
        # PT 파일에서 임베딩 데이터 로드
        pt_data = None
        if pt_file_path and os.path.exists(pt_file_path):
            try:
                import torch
                pt_data = torch.load(pt_file_path, map_location='cpu')
                
                # PyTorch 텐서를 JSON 직렬화 가능한 형태로 변환
                if 'z' in pt_data and hasattr(pt_data['z'], 'tolist'):
                    pt_data['z'] = pt_data['z'].tolist()
                if 'node_type' in pt_data and hasattr(pt_data['node_type'], 'tolist'):
                    pt_data['node_type'] = pt_data['node_type'].tolist()
                
                print(f"✅ 임베딩 데이터 로드 완료: {len(pt_data.get('z', []))}개 벡터")
            except Exception as e:
                print(f"⚠️ 임베딩 데이터 로드 실패: {e}")
                pt_data = None
        
        # pt_data 구성
        pt_payload = {"scene_graph": scene_data.get('scene_graph', {})}
        if pt_data:
            pt_payload.update(pt_data)
        
        scene_payload = {
            "video_unique_id": video_unique_id,
            "scene_data": {
                "scene_number": f"{start_frame}-{end_frame}",
                "scene_place": scene_meta.get('scene_place'),
                "scene_time": scene_meta.get('scene_time'),
                "scene_atmosphere": scene_meta.get('scene_atmosphere'),
                "start_frame": start_frame,
                "end_frame": end_frame
            },
            "pt_data": pt_payload
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/scenes", json=scene_payload)
            if response.status_code == 200:
                result = response.json()
                scene_id = result.get('scene_id')
                print(f"✅ 장면 생성 성공: ID {scene_id}")
                
                # 노드 데이터 저장
                if scene_id:
                    self._save_scene_nodes(scene_id, scene_data.get('scene_graph', {}))
                
                return scene_id
            else:
                print(f"❌ 장면 생성 실패: {response.text}")
                return None
        except Exception as e:
            print(f"❌ 장면 생성 오류: {e}")
            return None
    
    def _save_scene_nodes(self, scene_id: int, scene_graph: Dict[str, Any], pt_data: Dict[str, Any] = None):
        """장면의 노드 데이터들을 개별적으로 저장 (API를 통한 접근)"""
        print(f"🔗 장면 노드 데이터 저장: Scene ID {scene_id}")
        
        try:
            # 1. 객체 노드 저장
            objects = scene_graph.get('objects', [])
            if objects:
                self._save_objects(scene_id, objects)
            
            # 2. 이벤트 노드 저장
            events = scene_graph.get('events', [])
            if events:
                self._save_events(scene_id, events)
            
            # 3. 공간 관계 저장
            spatial = scene_graph.get('spatial', [])
            if spatial:
                self._save_spatial(scene_id, spatial)
            
            # 4. 시간 관계 저장
            temporal = scene_graph.get('temporal', [])
            if temporal:
                self._save_temporal(scene_id, temporal)
            
            # 5. 임베딩 데이터 저장
            if pt_data and 'z' in pt_data and 'orig_id' in pt_data:
                self._save_embeddings(scene_id, pt_data)
            
            print(f"✅ 모든 노드 데이터 저장 완료")
            
        except Exception as e:
            print(f"❌ 노드 데이터 저장 실패: {e}")
    
    def _save_objects(self, scene_id: int, objects: List[Dict[str, Any]]):
        """객체 노드 저장"""
        print(f"👥 객체 노드 저장: {len(objects)}개")
        
        for obj in objects:
            object_data = {
                "scene_id": scene_id,
                "object_id": obj.get('object_id'),
                "super_type": obj.get('super_type'),
                "type_of": obj.get('type of'),  # JSON의 'type of' 필드
                "label": obj.get('label'),
                "attributes": obj.get('attributes', {})
            }
            
            try:
                response = requests.post(f"{self.api_base_url}/objects", json=object_data)
                if response.status_code == 200:
                    print(f"  ✅ 객체 저장: {obj.get('label')}")
                else:
                    print(f"  ❌ 객체 저장 실패: {obj.get('label')} - {response.text}")
            except Exception as e:
                print(f"  ❌ 객체 저장 오류: {obj.get('label')} - {e}")
    
    def _save_events(self, scene_id: int, events: List[Dict[str, Any]]):
        """이벤트 노드 저장"""
        print(f"🎬 이벤트 노드 저장: {len(events)}개")
        
        for event in events:
            event_data = {
                "scene_id": scene_id,
                "event_id": event.get('event_id'),
                "subject_id": event.get('subject'),
                "verb": event.get('verb'),
                "object_id": event.get('object'),
                "attributes": {"attribute": event.get('attribute', '')}
            }
            
            try:
                response = requests.post(f"{self.api_base_url}/events", json=event_data)
                if response.status_code == 200:
                    print(f"  ✅ 이벤트 저장: {event.get('verb')}")
                else:
                    print(f"  ❌ 이벤트 저장 실패: {event.get('verb')} - {response.text}")
            except Exception as e:
                print(f"  ❌ 이벤트 저장 오류: {event.get('verb')} - {e}")
    
    def _save_spatial(self, scene_id: int, spatial: List[Dict[str, Any]]):
        """공간 관계 저장"""
        print(f"📍 공간 관계 저장: {len(spatial)}개")
        
        for rel in spatial:
            spatial_data = {
                "scene_id": scene_id,
                "spatial_id": rel.get('spatial_id'),
                "subject_id": rel.get('subject'),
                "predicate": rel.get('predicate'),
                "object_id": rel.get('object')
            }
            
            try:
                response = requests.post(f"{self.api_base_url}/spatial", json=spatial_data)
                if response.status_code == 200:
                    print(f"  ✅ 공간 관계 저장: {rel.get('predicate')}")
                else:
                    print(f"  ❌ 공간 관계 저장 실패: {rel.get('predicate')} - {response.text}")
            except Exception as e:
                print(f"  ❌ 공간 관계 저장 오류: {rel.get('predicate')} - {e}")
    
    def _save_temporal(self, scene_id: int, temporal: List[Dict[str, Any]]):
        """시간 관계 저장"""
        print(f"⏰ 시간 관계 저장: {len(temporal)}개")
        
        for rel in temporal:
            temporal_data = {
                "scene_id": scene_id,
                "temporal_id": rel.get('temporal_id'),
                "subject_id": rel.get('subject'),
                "predicate": rel.get('predicate'),
                "object_id": rel.get('object')
            }
            
            try:
                response = requests.post(f"{self.api_base_url}/temporal", json=temporal_data)
                if response.status_code == 200:
                    print(f"  ✅ 시간 관계 저장: {rel.get('predicate')}")
                else:
                    print(f"  ❌ 시간 관계 저장 실패: {rel.get('predicate')} - {response.text}")
            except Exception as e:
                print(f"  ❌ 시간 관계 저장 오류: {rel.get('predicate')} - {e}")
    
    def _save_embeddings(self, scene_id: int, pt_data: Dict[str, Any]):
        """임베딩 데이터 저장"""
        print(f"🔗 임베딩 데이터 저장: {len(pt_data.get('z', []))}개 벡터")
        
        try:
            embeddings = pt_data['z']
            orig_ids = pt_data['orig_id']
            
            for i, orig_id in enumerate(orig_ids):
                # ID 0은 특별한 노드이므로 건너뛰기
                if orig_id == 0:
                    continue
                
                # 노드 타입 결정 (orig_id 기반)
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
                
                # 임베딩 데이터 저장
                embedding_data = {
                    "node_id": orig_id,
                    "node_type": node_type,
                    "embedding": embeddings[i]
                }
                
                response = requests.post(f"{self.api_base_url}/embeddings", json=embedding_data)
                if response.status_code == 200:
                    print(f"  ✅ 임베딩 저장: {node_type} {orig_id}")
                else:
                    print(f"  ❌ 임베딩 저장 실패: {response.text}")
            
            print(f"✅ 임베딩 데이터 저장 완료")
            
        except Exception as e:
            print(f"❌ 임베딩 데이터 저장 실패: {e}")
    
    def _generate_video_id(self, drama_name: str, episode_number: str) -> int:
        """비디오 고유 ID 생성 (간단한 방식)"""
        import hashlib
        
        # SHA256 해시 사용 (충돌 확률 매우 낮음)
        combined = f"{drama_name}_{episode_number}".encode('utf-8')
        hash_value = hashlib.sha256(combined).hexdigest()
        
        # 8자리 숫자로 제한
        video_id = int(hash_value[:8], 16) % 100000000
        
        print(f"🔑 생성된 video_unique_id: {video_id}")
        return video_id
    
    def _get_video_unique_id_from_id(self, video_id: int) -> int:
        """비디오 ID로부터 video_unique_id 조회"""
        try:
            response = requests.get(f"{self.api_base_url}/videos")
            if response.status_code == 200:
                videos = response.json()
                for video in videos:
                    if video.get('id') == video_id:
                        return video.get('video_unique_id')
        except Exception as e:
            print(f"⚠️  video_unique_id 조회 실패: {e}")
        
        # 조회 실패 시 기본값 반환
        return 1001
    
    def upload_scene_graph(self, file_path: str) -> bool:
        """장면 그래프 데이터 전체 업로드 (임베딩 포함)"""
        print("🚀 장면 그래프 데이터 업로드 시작")
        print("=" * 50)
        
        try:
            # 1. 파일명에서 정보 파싱
            filename = os.path.basename(file_path)
            file_info = self.parse_filename(filename)
            
            # 2. JSON 데이터 로드
            scene_data = self.load_scene_graph_data(file_path)
            
            # 3. PT 파일 경로 생성
            pt_file_path = file_path.replace('.json', '.pt')
            
            # 4. 비디오 생성
            video_id = self.create_or_update_video(
                file_info['drama_name'], 
                file_info['episode_number']
            )
            
            if not video_id:
                print("❌ 비디오 생성 실패로 업로드 중단")
                return False
            
            # 5. PT 파일에서 임베딩 데이터 로드
            pt_data = None
            if os.path.exists(pt_file_path):
                try:
                    import torch
                    pt_data = torch.load(pt_file_path, map_location='cpu')
                    
                    # PyTorch 텐서를 JSON 직렬화 가능한 형태로 변환
                    if 'z' in pt_data and hasattr(pt_data['z'], 'tolist'):
                        pt_data['z'] = pt_data['z'].tolist()
                    if 'node_type' in pt_data and hasattr(pt_data['node_type'], 'tolist'):
                        pt_data['node_type'] = pt_data['node_type'].tolist()
                    
                    print(f"✅ 임베딩 데이터 로드 완료: {len(pt_data.get('z', []))}개 벡터")
                except Exception as e:
                    print(f"⚠️ 임베딩 데이터 로드 실패: {e}")
                    pt_data = None
            
            # 6. 장면 생성
            scene_id = self.create_scene(
                video_id,
                scene_data,
                file_info['start_frame'],
                file_info['end_frame']
            )
            
            if not scene_id:
                print("❌ 장면 생성 실패")
                return False
            
            # 7. 장면 노드 데이터 저장 (임베딩 포함)
            self._save_scene_nodes(scene_id, scene_data.get('scene_graph', {}), pt_data)
            
            # 8. 결과 요약
            print("\n" + "=" * 50)
            print("✅ 장면 그래프 데이터 업로드 완료!")
            print(f"📺 비디오: {file_info['drama_name']} {file_info['episode_number']}")
            print(f"🎭 장면: 프레임 {file_info['start_frame']}-{file_info['end_frame']}")
            print(f"🆔 비디오 ID: {video_id}, 장면 ID: {scene_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return False

def main():
    """메인 실행 함수"""
    print("🎬 Scene Graph Database 업로더")
    print("=" * 50)
    
    # API 서버 상태 확인
    uploader = SceneGraphUploader()
    
    try:
        response = requests.get(f"{uploader.api_base_url}/health")
        if response.status_code != 200:
            print("❌ API 서버가 실행되지 않았습니다.")
            print("💡 docker-compose up -d로 서버를 먼저 시작해주세요.")
            return
        print("✅ API 서버 연결 확인")
    except Exception as e:
        print(f"❌ API 서버 연결 실패: {e}")
        return
    
    # 테스트 데이터 파일 경로 (컨테이너 환경에 맞게)
    test_file = "test/data/Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json"
    
    if not os.path.exists(test_file):
        print(f"❌ 테스트 데이터 파일을 찾을 수 없습니다: {test_file}")
        print("💡 현재 디렉토리에서 실행해주세요.")
        print(f"💡 현재 디렉토리: {os.getcwd()}")
        print(f"💡 사용 가능한 파일들:")
        try:
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith('.json'):
                        print(f"    - {os.path.join(root, file)}")
        except Exception as e:
            print(f"    파일 목록 조회 실패: {e}")
        return
    
    print(f"📁 테스트 데이터 파일: {test_file}")
    
    # 장면 그래프 업로드 실행
    success = uploader.upload_scene_graph(test_file)
    
    if success:
        print("\n🎉 업로드가 성공적으로 완료되었습니다!")
        print("💡 이제 API를 통해 저장된 데이터를 확인할 수 있습니다.")
        
        # 저장된 데이터 확인
        print("\n📊 저장된 데이터 확인:")
        try:
            response = requests.get(f"{uploader.api_base_url}/videos")
            if response.status_code == 200:
                videos = response.json()
                print(f"✅ 비디오 {len(videos)}개:")
                for video in videos:
                    print(f"  - {video['drama_name']} {video['episode_number']} (ID: {video['id']})")
        except Exception as e:
            print(f"⚠️  데이터 확인 실패: {e}")
    else:
        print("\n💥 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
