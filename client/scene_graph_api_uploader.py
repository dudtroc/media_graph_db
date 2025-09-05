#!/usr/bin/env python3
"""
장면 그래프 데이터 API 업로더
JSON 파일에서 장면 그래프 데이터를 읽어와서 API를 통해 저장
"""

import json
import os
import re
import sys
import torch
import numpy as np
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class SceneGraphAPIUploader:
    """장면 그래프 데이터 API 업로더 클래스"""
    
    def __init__(self, api_base_url: str = None):
        """초기화"""
        self.api_base_url = api_base_url or os.getenv("API_URL", "http://localhost:8000")
        self.session = requests.Session()
        print(f"🌐 API 서버 URL: {self.api_base_url}")
    
    def health_check(self) -> bool:
        """API 서버 헬스 체크"""
        try:
            response = self.session.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                print("✅ API 서버 연결 성공")
                return True
            else:
                print(f"❌ API 서버 응답 오류: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API 서버 연결 실패: {e}")
            return False
    
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
    
    def create_video_via_api(self, drama_name: str, episode_number: str) -> Optional[Dict[str, Any]]:
        """API를 통해 비디오 생성"""
        print(f"🎬 API를 통한 비디오 생성: {drama_name} {episode_number}")
        
        try:
            # video_unique_id 생성
            video_unique_id = self._generate_video_id(drama_name, episode_number)
            
            # API 요청 데이터
            video_data = {
                "video_unique_id": video_unique_id,
                "drama_name": drama_name,
                "episode_number": episode_number
            }
            
            # API 호출
            response = self.session.post(f"{self.api_base_url}/videos", json=video_data)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 비디오 생성 성공: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 내용: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ 비디오 생성 오류: {e}")
            return None
    
    def create_scene_via_api(self, video_unique_id: int, scene_data: Dict[str, Any], 
                           start_frame: int, end_frame: int, pt_file_path: str = None) -> Optional[int]:
        """API를 통해 장면 데이터 생성 (임베딩 포함)"""
        print(f"🎭 API를 통한 장면 생성: 프레임 {start_frame}-{end_frame}")
        
        # 장면 메타데이터 준비
        scene_meta = scene_data.get('scene_graph', {}).get('meta', {})
        
        # PT 파일에서 임베딩 데이터 로드
        pt_data = None
        if pt_file_path and os.path.exists(pt_file_path):
            try:
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
        
        # 장면 데이터 구성
        scene_payload = {
            "scene_number": f"{start_frame}-{end_frame}",
            "scene_place": scene_meta.get('scene_place'),
            "scene_time": scene_meta.get('scene_time'),
            "scene_atmosphere": scene_meta.get('scene_atmosphere'),
            "start_frame": start_frame,
            "end_frame": end_frame
        }
        
        try:
            # API 요청 데이터
            scene_request = {
                "video_unique_id": video_unique_id,
                "scene_data": scene_payload,
                "pt_data": pt_data
            }
            
            # API 호출
            response = self.session.post(f"{self.api_base_url}/scenes", json=scene_request)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 장면 생성 성공: {result}")
            return result.get('scene_id')
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 내용: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ 장면 생성 오류: {e}")
            return None
    
    def create_nodes_via_api(self, scene_id: int, scene_graph: Dict[str, Any]):
        """API를 통해 장면의 노드 데이터들을 개별적으로 저장"""
        print(f"🔗 API를 통한 장면 노드 데이터 저장: Scene ID {scene_id}")
        
        try:
            # 1. 객체 노드 저장
            objects = scene_graph.get('objects', [])
            if objects:
                self._create_objects_via_api(scene_id, objects)
            
            # 2. 이벤트 노드 저장
            events = scene_graph.get('events', [])
            if events:
                self._create_events_via_api(scene_id, events)
            
            # 3. 공간 관계 저장
            spatial = scene_graph.get('spatial', [])
            if spatial:
                self._create_spatial_via_api(scene_id, spatial)
            
            # 4. 시간 관계 저장
            temporal = scene_graph.get('temporal', [])
            if temporal:
                self._create_temporal_via_api(scene_id, temporal)
            
            print(f"✅ 모든 노드 데이터 저장 완료")
            
        except Exception as e:
            print(f"❌ 노드 데이터 저장 실패: {e}")
    
    def _create_objects_via_api(self, scene_id: int, objects: List[Dict[str, Any]]):
        """API를 통해 객체 노드 저장"""
        print(f"👥 API를 통한 객체 노드 저장: {len(objects)}개")
        
        for obj in objects:
            try:
                object_data = {
                    "scene_id": scene_id,
                    "object_id": obj.get('object_id'),
                    "super_type": obj.get('super_type'),
                    "type_of": obj.get('type of'),  # JSON의 'type of' 필드
                    "label": obj.get('label'),
                    "attributes": obj.get('attributes', {})
                }
                
                response = self.session.post(f"{self.api_base_url}/objects", json=object_data)
                response.raise_for_status()
                
                result = response.json()
                print(f"  ✅ 객체 저장: {obj.get('label')} (ID: {result.get('object_id')})")
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 객체 저장 API 오류: {obj.get('label')} - {e}")
            except Exception as e:
                print(f"  ❌ 객체 저장 오류: {obj.get('label')} - {e}")
    
    def _create_events_via_api(self, scene_id: int, events: List[Dict[str, Any]]):
        """API를 통해 이벤트 노드 저장"""
        print(f"🎬 API를 통한 이벤트 노드 저장: {len(events)}개")
        
        for i, event in enumerate(events):
            try:
                event_data = {
                    "scene_id": scene_id,
                    "event_id": str(event.get('event_id', f"EVT_{i}")),  # 문자열로 변환
                    "subject_id": str(event.get('subject', '')),  # 문자열로 변환
                    "verb": event.get('verb', ''),
                    "object_id": str(event.get('object', '')) if event.get('object') else None,  # 문자열로 변환
                    "attributes": {"attribute": event.get('attribute', '')}
                }
                
                response = self.session.post(f"{self.api_base_url}/events", json=event_data)
                response.raise_for_status()
                
                result = response.json()
                print(f"  ✅ 이벤트 저장: {event.get('verb')} (ID: {result.get('event_id')})")
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 이벤트 저장 API 오류: {event.get('verb')} - {e}")
            except Exception as e:
                print(f"  ❌ 이벤트 저장 오류: {event.get('verb')} - {e}")
    
    def _create_spatial_via_api(self, scene_id: int, spatial: List[Dict[str, Any]]):
        """API를 통해 공간 관계 저장"""
        print(f"📍 API를 통한 공간 관계 저장: {len(spatial)}개")
        
        for i, rel in enumerate(spatial):
            try:
                spatial_data = {
                    "scene_id": scene_id,
                    "spatial_id": str(rel.get('spatial_id', f"SPAT_{i}")),  # 문자열로 변환
                    "subject_id": str(rel.get('subject', '')),  # 문자열로 변환
                    "predicate": rel.get('predicate', ''),
                    "object_id": str(rel.get('object', ''))  # 문자열로 변환
                }
                
                response = self.session.post(f"{self.api_base_url}/spatial", json=spatial_data)
                response.raise_for_status()
                
                result = response.json()
                print(f"  ✅ 공간 관계 저장: {rel.get('predicate')} (ID: {result.get('spatial_id')})")
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 공간 관계 저장 API 오류: {rel.get('predicate')} - {e}")
            except Exception as e:
                print(f"  ❌ 공간 관계 저장 오류: {rel.get('predicate')} - {e}")
    
    def _create_temporal_via_api(self, scene_id: int, temporal: List[Dict[str, Any]]):
        """API를 통해 시간 관계 저장"""
        print(f"⏰ API를 통한 시간 관계 저장: {len(temporal)}개")
        
        for i, rel in enumerate(temporal):
            try:
                temporal_data = {
                    "scene_id": scene_id,
                    "temporal_id": str(rel.get('temporal_id', f"TEMP_{i}")),  # 문자열로 변환
                    "subject_id": str(rel.get('subject', '')),  # 문자열로 변환
                    "predicate": rel.get('predicate', ''),
                    "object_id": str(rel.get('object', ''))  # 문자열로 변환
                }
                
                response = self.session.post(f"{self.api_base_url}/temporal", json=temporal_data)
                response.raise_for_status()
                
                result = response.json()
                print(f"  ✅ 시간 관계 저장: {rel.get('predicate')} (ID: {result.get('temporal_id')})")
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 시간 관계 저장 API 오류: {rel.get('predicate')} - {e}")
            except Exception as e:
                print(f"  ❌ 시간 관계 저장 오류: {rel.get('predicate')} - {e}")
    
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
    
    def upload_scene_graph(self, file_path: str) -> bool:
        """장면 그래프 데이터 전체 업로드 (API 통신)"""
        print("🚀 장면 그래프 데이터 API 업로드 시작")
        print("=" * 50)
        
        try:
            # 1. API 서버 헬스 체크
            if not self.health_check():
                print("❌ API 서버에 연결할 수 없습니다.")
                return False
            
            # 2. 파일명에서 정보 파싱
            filename = os.path.basename(file_path)
            file_info = self.parse_filename(filename)
            
            # 3. JSON 데이터 로드
            scene_data = self.load_scene_graph_data(file_path)
            
            # 4. PT 파일 경로 생성
            pt_file_path = file_path.replace('.json', '.pt')
            
            # 5. 비디오 생성 (API)
            video_result = self.create_video_via_api(
                file_info['drama_name'], 
                file_info['episode_number']
            )
            
            if not video_result:
                print("❌ 비디오 생성 실패로 업로드 중단")
                return False
            
            # 서버에서 반환된 실제 video_unique_id 사용
            video_id = video_result.get('video_id')
            video_unique_id = video_result.get('video_unique_id')
            print(f"✅ 사용할 video_id: {video_id}, video_unique_id: {video_unique_id}")
            
            # 6. 장면 생성 (API) - 서버에서 반환된 실제 video_unique_id 사용
            scene_id = self.create_scene_via_api(
                video_unique_id,  # 서버에서 반환된 실제 video_unique_id
                scene_data,
                file_info['start_frame'],
                file_info['end_frame'],
                pt_file_path
            )
            
            if not scene_id:
                print("❌ 장면 생성 실패")
                return False
            
            # 7. 장면 노드 데이터 저장 (API)
            self.create_nodes_via_api(scene_id, scene_data.get('scene_graph', {}))
            
            # 8. 결과 요약
            print("\n" + "=" * 50)
            print("✅ 장면 그래프 데이터 API 업로드 완료!")
            print(f"📺 비디오: {file_info['drama_name']} {file_info['episode_number']}")
            print(f"🎭 장면: 프레임 {file_info['start_frame']}-{file_info['end_frame']}")
            print(f"🆔 비디오 ID: {video_id}, 장면 ID: {scene_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return False

def main():
    """메인 실행 함수"""
    print("🎬 Scene Graph Database API 업로더")
    print("=" * 50)
    
    # API 업로더 초기화
    try:
        uploader = SceneGraphAPIUploader()
        print("✅ API 업로더 초기화 완료")
    except Exception as e:
        print(f"❌ API 업로더 초기화 실패: {e}")
        print("💡 API 서버가 실행 중인지 확인해주세요.")
        return
    
    # 테스트 데이터 파일 경로
    test_file = "data/Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json"
    
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
        print("\n🎉 API 업로드가 성공적으로 완료되었습니다!")
        print("💡 이제 API를 통해 저장된 데이터를 확인할 수 있습니다.")
        
        # 저장된 데이터 확인
        print("\n📊 저장된 데이터 확인:")
        try:
            response = uploader.session.get(f"{uploader.api_base_url}/videos")
            if response.status_code == 200:
                videos = response.json()
                print(f"✅ 비디오 {len(videos)}개:")
                for video in videos:
                    print(f"  - {video['drama_name']} {video['episode_number']} (ID: {video['id']})")
        except Exception as e:
            print(f"⚠️  데이터 확인 실패: {e}")
    else:
        print("\n💥 API 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
