#!/usr/bin/env python3
"""
데이터 삭제 예시 스크립트
SceneGraphClient를 사용한 다양한 데이터 삭제 방법을 보여줍니다.
"""

from scene_graph_client import SceneGraphClient

def example_clear_all_data():
    """모든 데이터 삭제 예시"""
    print("🗑️ 모든 데이터 삭제 예시")
    print("-" * 40)
    
    client = SceneGraphClient()
    
    # 1. 현재 상태 확인
    print("1. 현재 데이터베이스 상태 확인:")
    summary = client.get_data_summary()
    if summary:
        print(f"   - 비디오: {summary['total_videos']}개")
        print(f"   - 장면: {summary['total_scenes']}개")
        print(f"   - 객체: {summary['total_objects']}개")
        print(f"   - 이벤트: {summary['total_events']}개")
        print(f"   - 임베딩: {summary['total_embeddings']}개")
    
    # 2. 비디오 목록 조회
    print("\n2. 비디오 목록 조회:")
    videos = client.get_videos()
    for i, video in enumerate(videos[:5], 1):  # 처음 5개만 표시
        print(f"   {i}. {video['drama_name']} {video['episode_number']} (ID: {video['video_unique_id']})")
    if len(videos) > 5:
        print(f"   ... 총 {len(videos)}개")
    
    # 3. 모든 비디오 삭제 (확인 필요)
    print(f"\n3. 모든 비디오 삭제 (총 {len(videos)}개):")
    for i, video in enumerate(videos, 1):
        video_id = video['video_unique_id']
        drama_name = video['drama_name']
        episode_number = video['episode_number']
        
        print(f"   [{i}/{len(videos)}] 삭제 중: {drama_name} {episode_number}")
        
        # 실제 삭제 (확인 없이)
        success = client.delete_video(video_id, confirm=True)
        if success:
            print(f"      ✅ 삭제 완료")
        else:
            print(f"      ❌ 삭제 실패")
    
    # 4. 최종 확인
    print(f"\n4. 최종 상태 확인:")
    final_summary = client.get_data_summary()
    if final_summary:
        print(f"   - 비디오: {final_summary['total_videos']}개")
        print(f"   - 장면: {final_summary['total_scenes']}개")
        print(f"   - 객체: {final_summary['total_objects']}개")
        print(f"   - 이벤트: {final_summary['total_events']}개")
        print(f"   - 임베딩: {final_summary['total_embeddings']}개")

def example_clear_specific_videos():
    """특정 비디오들만 삭제 예시"""
    print("🗑️ 특정 비디오 삭제 예시")
    print("-" * 40)
    
    client = SceneGraphClient()
    
    # 1. 비디오 목록 조회
    videos = client.get_videos()
    if not videos:
        print("삭제할 비디오가 없습니다.")
        return
    
    # 2. 처음 3개 비디오만 삭제
    target_videos = videos[:3]
    video_ids = [v['video_unique_id'] for v in target_videos]
    
    print(f"삭제할 비디오 목록 ({len(target_videos)}개):")
    for video in target_videos:
        print(f"   - {video['drama_name']} {video['episode_number']} (ID: {video['video_unique_id']})")
    
    # 3. 삭제 실행
    print(f"\n삭제 실행:")
    for video in target_videos:
        video_id = video['video_unique_id']
        print(f"   삭제 중: {video['drama_name']} {video['episode_number']}")
        
        success = client.delete_video(video_id, confirm=True)
        if success:
            print(f"      ✅ 삭제 완료")
        else:
            print(f"      ❌ 삭제 실패")

def example_clear_by_drama_name():
    """드라마 이름으로 삭제 예시"""
    print("🗑️ 드라마 이름으로 삭제 예시")
    print("-" * 40)
    
    client = SceneGraphClient()
    
    # 1. 특정 드라마의 모든 에피소드 찾기
    target_drama = "Kingdom"  # 삭제할 드라마 이름
    
    videos = client.get_videos()
    target_videos = [v for v in videos if target_drama.lower() in v['drama_name'].lower()]
    
    if not target_videos:
        print(f"'{target_drama}' 드라마를 찾을 수 없습니다.")
        return
    
    print(f"'{target_drama}' 드라마의 에피소드들 ({len(target_videos)}개):")
    for video in target_videos:
        print(f"   - {video['drama_name']} {video['episode_number']} (ID: {video['video_unique_id']})")
    
    # 2. 삭제 실행
    print(f"\n삭제 실행:")
    for video in target_videos:
        video_id = video['video_unique_id']
        print(f"   삭제 중: {video['drama_name']} {video['episode_number']}")
        
        success = client.delete_video(video_id, confirm=True)
        if success:
            print(f"      ✅ 삭제 완료")
        else:
            print(f"      ❌ 삭제 실패")

def main():
    """메인 실행 함수"""
    print("🗑️ 데이터 삭제 예시 스크립트")
    print("=" * 50)
    
    while True:
        print("\n사용 가능한 예시:")
        print("1. 모든 데이터 삭제")
        print("2. 특정 비디오들만 삭제 (처음 3개)")
        print("3. 드라마 이름으로 삭제 (Kingdom)")
        print("4. 현재 상태만 확인")
        print("5. 종료")
        
        choice = input("\n예시를 선택하세요 (1-5): ").strip()
        
        if choice == "1":
            example_clear_all_data()
        elif choice == "2":
            example_clear_specific_videos()
        elif choice == "3":
            example_clear_by_drama_name()
        elif choice == "4":
            from scene_graph_client import SceneGraphClient
            client = SceneGraphClient()
            client.check_all_data()
        elif choice == "5":
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
