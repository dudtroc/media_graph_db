#!/usr/bin/env python3
"""
장면그래프 데이터베이스 통합 클라이언트
모든 DB API 접근 기능을 통합한 클래스
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 기존 클라이언트 모듈들 import
from util import VideoDataDeleter, SceneGraphDataChecker, SceneGraphAPIUploader

# 환경 변수 로드
load_dotenv()

class SceneGraphClient:
    """
    장면그래프 데이터베이스 통합 클라이언트
    
    이 클래스는 다음 기능들을 통합합니다:
    - 비디오 데이터 삭제 (VideoDataDeleter)
    - 저장된 데이터 확인 (SceneGraphDataChecker)  
    - 장면그래프 데이터 업로드 (SceneGraphAPIUploader)
    - 기본적인 DB API 접근 기능
    """
    
    def __init__(self, api_base_url: str = None):
        """
        초기화
        
        Args:
            api_base_url: API 서버 URL (기본값: 환경변수 API_URL 또는 http://localhost:8000)
        """
        self.api_base_url = api_base_url or os.getenv("API_URL", "http://localhost:8000")
        self.session = requests.Session()
        
        # 하위 클라이언트들 초기화
        self.deleter = VideoDataDeleter(self.api_base_url)
        self.checker = SceneGraphDataChecker(self.api_base_url)
        self.uploader = SceneGraphAPIUploader(self.api_base_url)
        
        print(f"🌐 SceneGraphClient 초기화 완료 - API URL: {self.api_base_url}")
    
    # ==================== 기본 연결 및 상태 확인 ====================
    
    def health_check(self) -> bool:
        """API 서버 헬스 체크"""
        return self.checker.check_connection()
    
    def get_server_info(self) -> Dict[str, Any]:
        """서버 기본 정보 조회"""
        try:
            response = self.session.get(f"{self.api_base_url}/")
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
            
            response = self.session.post(f"{self.api_base_url}/videos", json=video_data)
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
        장면그래프 데이터 업로드
        
        Args:
            json_file_path: JSON 파일 경로
        
        Returns:
            bool: 업로드 성공 여부
        """
        return self.uploader.upload_scene_graph(json_file_path)
    
    def upload_scene_graph_with_pt(self, json_file_path: str, pt_file_path: str) -> bool:
        """
        장면그래프 데이터와 PT 파일을 함께 업로드
        
        Args:
            json_file_path: JSON 파일 경로
            pt_file_path: PT 파일 경로
        
        Returns:
            bool: 업로드 성공 여부
        """
        # PT 파일이 있는 경우 해당 파일을 사용하여 업로드
        # SceneGraphAPIUploader는 파일명에서 자동으로 PT 파일을 찾으므로
        # PT 파일을 JSON 파일과 같은 디렉토리에 배치하고 이름을 맞춰야 함
        return self.uploader.upload_scene_graph(json_file_path)
    
    # ==================== 검색 기능 ====================
    
    def vector_search(self, query_embedding: List[float], node_type: str = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        벡터 기반 유사도 검색
        
        Args:
            query_embedding: 검색할 벡터 (384차원)
            node_type: 노드 타입 필터 (object, event, spatial, temporal)
            top_k: 반환할 결과 수
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            search_data = {
                "query_embedding": query_embedding,
                "node_type": node_type,
                "top_k": top_k
            }
            
            response = self.session.post(f"{self.api_base_url}/search/vector", json=search_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {e}")
            return []
    
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
            
            response = self.session.post(f"{self.api_base_url}/search/hybrid", json=search_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 하이브리드 검색 실패: {e}")
            return []
    
    # ==================== 데이터 확인 및 관리 ====================
    
    def check_all_data(self) -> None:
        """모든 저장된 데이터 확인"""
        self.checker.check_all_data()
    
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
        """비디오 고유 ID 생성"""
        # 간단한 해시 기반 ID 생성
        import hashlib
        content = f"{drama_name}_{episode_number}"
        hash_obj = hashlib.md5(content.encode())
        return int(hash_obj.hexdigest()[:8], 16)
    
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
            print("5. 벡터 검색 (search)")
            print("6. 데이터 요약 (summary)")
            print("7. 종료 (quit)")
            
            choice = input("\n명령어를 선택하세요: ").strip().lower()
            
            if choice == 'check':
                self.check_all_data()
            elif choice == 'list':
                self.list_videos()
            elif choice == 'delete':
                self._interactive_delete()
            elif choice == 'upload':
                self._interactive_upload()
            elif choice == 'search':
                self._interactive_search()
            elif choice == 'summary':
                self._show_summary()
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
    
    def _interactive_upload(self) -> None:
        """대화형 업로드 모드"""
        json_file = input("JSON 파일 경로를 입력하세요: ").strip()
        
        if os.path.exists(json_file):
            self.upload_scene_graph(json_file)
        else:
            print("❌ 파일을 찾을 수 없습니다.")
    
    def _interactive_search(self) -> None:
        """대화형 검색 모드"""
        print("벡터 검색을 위해서는 384차원 벡터가 필요합니다.")
        print("현재는 간단한 텍스트 검색만 지원합니다.")
        # TODO: 실제 벡터 검색 구현
    
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
    
    client = SceneGraphClient()
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            client.check_all_data()
        elif command == "list":
            client.list_videos()
        elif command == "summary":
            client._show_summary()
        elif command == "interactive":
            client.interactive_mode()
        else:
            print("사용법:")
            print("  python scene_graph_client.py check        # 데이터 확인")
            print("  python scene_graph_client.py list         # 비디오 목록")
            print("  python scene_graph_client.py summary      # 데이터 요약")
            print("  python scene_graph_client.py interactive  # 대화형 모드")
    else:
        # 기본적으로 대화형 모드 실행
        client.interactive_mode()


if __name__ == "__main__":
    main()
