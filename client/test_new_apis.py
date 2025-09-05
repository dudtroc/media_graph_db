#!/usr/bin/env python3
"""
새로 구현된 API들을 테스트하는 스크립트
- GET /videos/{video_unique_id} - 비디오 정보와 연결된 장면들
- GET /scenes/{scene_id} - 장면 그래프의 모든 노드 정보
"""

import os
import sys
import requests
import json
from typing import Dict, List, Any

# API 서버 기본 URL
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")

class NewAPITester:
    """새로 구현된 API들을 테스트하는 클래스"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """API 서버 헬스 체크"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API 서버 연결 성공")
                return True
            else:
                print(f"❌ API 서버 응답 오류: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API 서버 연결 실패: {e}")
            return False
    
    def test_video_with_scenes(self, video_unique_id: int) -> bool:
        """GET /videos/{video_unique_id} 테스트"""
        print(f"\n🎬 비디오 {video_unique_id}의 정보와 장면들 조회 테스트...")
        
        try:
            response = self.session.get(f"{self.base_url}/videos/{video_unique_id}")
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ 비디오 정보 조회 성공:")
            print(f"   📺 드라마: {data['drama_name']} {data['episode_number']}")
            print(f"   🆔 비디오 ID: {data['video_id']}, 고유 ID: {data['video_unique_id']}")
            print(f"   📅 생성일: {data['created_at']}")
            print(f"   🎭 장면 수: {data['scene_count']}개")
            
            if data['scenes']:
                print(f"\n   📋 장면 목록:")
                for i, scene in enumerate(data['scenes'], 1):
                    print(f"     {i}. 장면 ID: {scene['scene_id']}")
                    print(f"        - 번호: {scene['scene_number']}")
                    print(f"        - 장소: {scene['scene_place']}")
                    print(f"        - 시간: {scene['scene_time']}")
                    print(f"        - 분위기: {scene['scene_atmosphere']}")
                    print(f"        - 프레임: {scene['start_frame']}-{scene['end_frame']}")
                    print(f"        - 생성일: {scene['created_at']}")
            else:
                print("   📋 저장된 장면이 없습니다.")
            
            return True
            
        except Exception as e:
            print(f"❌ 비디오 정보 조회 실패: {e}")
            return False
    
    def test_scene_graph(self, scene_id: int) -> bool:
        """GET /scenes/{scene_id} 테스트"""
        print(f"\n🎭 장면 {scene_id}의 그래프 정보 조회 테스트...")
        
        try:
            response = self.session.get(f"{self.base_url}/scenes/{scene_id}")
            response.raise_for_status()
            
            data = response.json()
            scene = data['scene']
            summary = data['summary']
            
            print(f"✅ 장면 그래프 조회 성공:")
            print(f"   🎬 장면 정보:")
            print(f"     - ID: {scene['id']}")
            print(f"     - 번호: {scene['scene_number']}")
            print(f"     - 드라마: {scene['drama_name']} {scene['episode_number']}")
            print(f"     - 장소: {scene['scene_place']}")
            print(f"     - 시간: {scene['scene_time']}")
            print(f"     - 분위기: {scene['scene_atmosphere']}")
            print(f"     - 프레임: {scene['start_frame']}-{scene['end_frame']}")
            
            print(f"\n   📊 노드 요약:")
            print(f"     - 객체: {summary['total_objects']}개")
            print(f"     - 이벤트: {summary['total_events']}개")
            print(f"     - 공간관계: {summary['total_spatial']}개")
            print(f"     - 시간관계: {summary['total_temporal']}개")
            print(f"     - 임베딩: {summary['total_embeddings']}개")
            
            # 객체 노드들
            if data['objects']:
                print(f"\n   👥 객체 노드들 ({len(data['objects'])}개):")
                for obj in data['objects']:
                    print(f"     - {obj['label']} (ID: {obj['object_id']}, 타입: {obj['type_of']})")
            
            # 이벤트 노드들
            if data['events']:
                print(f"\n   🎬 이벤트 노드들 ({len(data['events'])}개):")
                for event in data['events']:
                    print(f"     - {event['verb']} (ID: {event['event_id']}, 주체: {event['subject_id']})")
            
            # 공간관계들
            if data['spatial']:
                print(f"\n   📍 공간관계들 ({len(data['spatial'])}개):")
                for rel in data['spatial']:
                    print(f"     - {rel['predicate']} (ID: {rel['spatial_id']}, 주체: {rel['subject_id']} → 대상: {rel['object_id']})")
            
            # 시간관계들
            if data['temporal']:
                print(f"\n   ⏰ 시간관계들 ({len(data['temporal'])}개):")
                for rel in data['temporal']:
                    print(f"     - {rel['predicate']} (ID: {rel['temporal_id']}, 주체: {rel['subject_id']} → 대상: {rel['object_id']})")
            
            # 임베딩들
            if data['embeddings']:
                print(f"\n   🔗 임베딩들 ({len(data['embeddings'])}개):")
                for emb in data['embeddings']:
                    print(f"     - 노드 ID: {emb['node_id']}, 타입: {emb['node_type']}, 차원: {emb['vector_length']}")
                    if emb['embedding'] and len(emb['embedding']) > 0:
                        print(f"       벡터 샘플: [{emb['embedding'][0]:.4f}, {emb['embedding'][1]:.4f}, ...]")
            
            return True
            
        except Exception as e:
            print(f"❌ 장면 그래프 조회 실패: {e}")
            return False
    
    def test_all_videos(self) -> bool:
        """모든 비디오들의 정보를 조회"""
        print(f"\n📺 모든 비디오들의 정보 조회 테스트...")
        
        try:
            response = self.session.get(f"{self.base_url}/videos")
            response.raise_for_status()
            
            videos = response.json()
            print(f"✅ 비디오 목록 조회 성공: {len(videos)}개")
            
            for video in videos:
                print(f"\n🎬 비디오: {video['drama_name']} {video['episode_number']} (ID: {video['video_unique_id']})")
                
                # 각 비디오의 상세 정보와 장면들 조회
                success = self.test_video_with_scenes(video['video_unique_id'])
                if not success:
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ 비디오 목록 조회 실패: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        print("🧪 새로운 API 테스트 시작")
        print("=" * 60)
        
        # 헬스 체크
        if not self.health_check():
            return False
        
        # 모든 비디오들의 정보 조회
        if not self.test_all_videos():
            return False
        
        # 특정 장면의 그래프 정보 조회 (첫 번째 장면)
        try:
            response = self.session.get(f"{self.base_url}/videos")
            videos = response.json()
            if videos:
                video = videos[0]
                video_id = video['video_unique_id']
                
                # 해당 비디오의 장면들 조회
                video_response = self.session.get(f"{self.base_url}/videos/{video_id}")
                video_data = video_response.json()
                
                if video_data['scenes']:
                    scene_id = video_data['scenes'][0]['scene_id']
                    if not self.test_scene_graph(scene_id):
                        return False
        except Exception as e:
            print(f"❌ 장면 그래프 테스트 실패: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 모든 새로운 API 테스트가 성공적으로 완료되었습니다!")
        return True

def main():
    """메인 실행 함수"""
    print("🚀 새로운 Scene Graph Database API 테스트")
    print("=" * 60)
    
    # 테스터 생성
    tester = NewAPITester()
    
    # 모든 테스트 실행
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
        print("💡 이제 Python 코드로 DB에 저장된 장면그래프와 임베딩 정보를 가져올 수 있습니다.")
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")
        print("💡 API 서버 설정과 엔드포인트를 확인해주세요.")

if __name__ == "__main__":
    main()
