#!/usr/bin/env python3
"""
통합 클라이언트 테스트 스크립트
SceneGraphClient의 기본 기능들을 테스트합니다.
"""

import os
import sys
from scene_graph_client import SceneGraphClient

def test_basic_connection():
    """기본 연결 테스트"""
    print("🔗 기본 연결 테스트")
    print("-" * 30)
    
    client = SceneGraphClient()
    
    # 헬스 체크
    if client.health_check():
        print("✅ API 서버 연결 성공")
        
        # 서버 정보 조회
        server_info = client.get_server_info()
        print(f"✅ 서버 정보: {server_info}")
        return True
    else:
        print("❌ API 서버 연결 실패")
        return False

def test_video_management():
    """비디오 관리 기능 테스트"""
    print("\n📺 비디오 관리 테스트")
    print("-" * 30)
    
    client = SceneGraphClient()
    
    # 비디오 목록 조회
    videos = client.get_videos()
    print(f"✅ 저장된 비디오 수: {len(videos)}개")
    
    if videos:
        # 첫 번째 비디오 정보 조회
        first_video = videos[0]
        video_info = client.get_video_info(first_video['video_unique_id'])
        if video_info:
            print(f"✅ 비디오 정보 조회 성공: {video_info['drama_name']} {video_info['episode_number']}")
        else:
            print("❌ 비디오 정보 조회 실패")
    else:
        print("ℹ️ 저장된 비디오가 없습니다.")
    
    return True

def test_scene_management():
    """장면 관리 기능 테스트"""
    print("\n🎭 장면 관리 테스트")
    print("-" * 30)
    
    client = SceneGraphClient()
    
    # 비디오 목록 조회
    videos = client.get_videos()
    if not videos:
        print("ℹ️ 테스트할 비디오가 없습니다.")
        return True
    
    # 첫 번째 비디오의 장면들 조회
    first_video = videos[0]
    scenes = client.get_scenes(first_video['id'])
    print(f"✅ 비디오 '{first_video['drama_name']}'의 장면 수: {len(scenes)}개")
    
    if scenes:
        # 첫 번째 장면의 상세 정보 조회
        first_scene = scenes[0]
        scene_graph = client.get_scene_graph(first_scene['id'])
        
        if scene_graph:
            print(f"✅ 장면 그래프 조회 성공:")
            print(f"   - 객체: {len(scene_graph.get('objects', []))}개")
            print(f"   - 이벤트: {len(scene_graph.get('events', []))}개")
            print(f"   - 공간관계: {len(scene_graph.get('spatial', []))}개")
            print(f"   - 시간관계: {len(scene_graph.get('temporal', []))}개")
            print(f"   - 임베딩: {len(scene_graph.get('embeddings', []))}개")
        else:
            print("❌ 장면 그래프 조회 실패")
    else:
        print("ℹ️ 테스트할 장면이 없습니다.")
    
    return True

def test_data_summary():
    """데이터 요약 기능 테스트"""
    print("\n📊 데이터 요약 테스트")
    print("-" * 30)
    
    client = SceneGraphClient()
    
    summary = client.get_data_summary()
    if summary:
        print("✅ 데이터 요약 조회 성공:")
        print(f"   - 비디오: {summary['total_videos']}개")
        print(f"   - 장면: {summary['total_scenes']}개")
        print(f"   - 객체: {summary['total_objects']}개")
        print(f"   - 이벤트: {summary['total_events']}개")
        print(f"   - 임베딩: {summary['total_embeddings']}개")
    else:
        print("❌ 데이터 요약 조회 실패")
    
    return True

def test_export_import():
    """데이터 내보내기/가져오기 테스트"""
    print("\n📁 데이터 내보내기/가져오기 테스트")
    print("-" * 30)
    
    client = SceneGraphClient()
    
    # 장면 목록 조회
    videos = client.get_videos()
    if not videos:
        print("ℹ️ 테스트할 데이터가 없습니다.")
        return True
    
    scenes = client.get_scenes(videos[0]['id'])
    if not scenes:
        print("ℹ️ 테스트할 장면이 없습니다.")
        return True
    
    # 첫 번째 장면 내보내기
    scene_id = scenes[0]['id']
    export_file = f"test_scene_{scene_id}.json"
    
    if client.export_scene_data(scene_id, export_file):
        print(f"✅ 장면 {scene_id} 내보내기 성공: {export_file}")
        
        # 파일이 생성되었는지 확인
        if os.path.exists(export_file):
            print(f"✅ 파일 생성 확인: {export_file}")
            
            # 테스트 파일 삭제
            os.remove(export_file)
            print(f"✅ 테스트 파일 삭제: {export_file}")
        else:
            print("❌ 파일이 생성되지 않았습니다.")
    else:
        print("❌ 장면 내보내기 실패")
    
    return True

def main():
    """메인 테스트 함수"""
    print("🧪 SceneGraphClient 통합 테스트")
    print("=" * 50)
    
    tests = [
        ("기본 연결", test_basic_connection),
        ("비디오 관리", test_video_management),
        ("장면 관리", test_scene_management),
        ("데이터 요약", test_data_summary),
        ("내보내기/가져오기", test_export_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 테스트 통과")
            else:
                print(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
    
    print("\n" + "=" * 50)
    print(f"테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return 0
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
