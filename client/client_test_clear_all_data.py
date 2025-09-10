#!/usr/bin/env python3
"""
데이터베이스의 모든 데이터를 삭제하는 스크립트
SceneGraphClient를 사용하여 안전하게 모든 비디오와 관련 데이터를 삭제합니다.
"""

import sys
import os
from scene_graph_client import SceneGraphClient

def clear_all_data(confirm: bool = False):
    """
    데이터베이스의 모든 데이터를 삭제
    
    Args:
        confirm: True이면 확인 없이 삭제, False이면 사용자 확인 후 삭제
    """
    print("🗑️ 데이터베이스 전체 데이터 삭제")
    print("=" * 60)
    
    # 클라이언트 초기화
    client = SceneGraphClient()
    
    # 1. API 서버 연결 확인
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return False
    
    # 2. 현재 데이터 요약 조회
    print("\n📊 현재 데이터베이스 상태:")
    summary = client.get_data_summary()
    if not summary:
        print("❌ 데이터 요약을 가져올 수 없습니다.")
        return False
    
    print(f"   - 비디오: {summary['total_videos']}개")
    print(f"   - 장면: {summary['total_scenes']}개")
    print(f"   - 객체: {summary['total_objects']}개")
    print(f"   - 이벤트: {summary['total_events']}개")
    print(f"   - 임베딩: {summary['total_embeddings']}개")
    
    if summary['total_videos'] == 0:
        print("ℹ️ 삭제할 데이터가 없습니다.")
        return True
    
    # 3. 비디오 목록 조회
    videos = client.get_videos()
    if not videos:
        print("ℹ️ 삭제할 비디오가 없습니다.")
        return True
    
    print(f"\n📺 삭제할 비디오 목록 ({len(videos)}개):")
    for i, video in enumerate(videos, 1):
        print(f"   {i}. {video['drama_name']} {video['episode_number']} (ID: {video['video_unique_id']})")
    
    # 4. 사용자 확인
    if not confirm:
        print(f"\n⚠️ 경고: 이 작업은 되돌릴 수 없습니다!")
        print(f"   - {len(videos)}개의 비디오와 모든 관련 데이터가 삭제됩니다.")
        print(f"   - 총 {summary['total_scenes']}개의 장면")
        print(f"   - 총 {summary['total_objects']}개의 객체")
        print(f"   - 총 {summary['total_events']}개의 이벤트")
        print(f"   - 총 {summary['total_embeddings']}개의 임베딩")
        
        user_input = input(f"\n정말로 모든 데이터를 삭제하시겠습니까? (yes/no): ").strip().lower()
        if user_input not in ['yes', 'y']:
            print("❌ 삭제가 취소되었습니다.")
            return False
    
    # 5. 비디오 삭제 실행
    print(f"\n🔄 삭제 시작...")
    deleted_count = 0
    failed_count = 0
    
    for i, video in enumerate(videos, 1):
        video_id = video['video_unique_id']
        drama_name = video['drama_name']
        episode_number = video['episode_number']
        
        print(f"\n[{i}/{len(videos)}] 삭제 중: {drama_name} {episode_number} (ID: {video_id})")
        
        try:
            success = client.delete_video(video_id, confirm=True)
            if success:
                deleted_count += 1
                print(f"   ✅ 삭제 완료")
            else:
                failed_count += 1
                print(f"   ❌ 삭제 실패")
        except Exception as e:
            failed_count += 1
            print(f"   ❌ 삭제 오류: {e}")
    
    # 6. 삭제 결과 요약
    print(f"\n" + "=" * 60)
    print(f"🗑️ 삭제 완료!")
    print(f"   - 성공: {deleted_count}개")
    print(f"   - 실패: {failed_count}개")
    print(f"   - 총 처리: {len(videos)}개")
    
    # 7. 최종 확인
    print(f"\n🔍 최종 데이터베이스 상태 확인:")
    final_summary = client.get_data_summary()
    if final_summary:
        print(f"   - 비디오: {final_summary['total_videos']}개")
        print(f"   - 장면: {final_summary['total_scenes']}개")
        print(f"   - 객체: {final_summary['total_objects']}개")
        print(f"   - 이벤트: {final_summary['total_events']}개")
        print(f"   - 임베딩: {final_summary['total_embeddings']}개")
        
        if final_summary['total_videos'] == 0:
            print("✅ 모든 데이터가 성공적으로 삭제되었습니다!")
            return True
        else:
            print("⚠️ 일부 데이터가 남아있습니다.")
            return False
    else:
        print("❌ 최종 확인에 실패했습니다.")
        return False

def clear_specific_videos(video_ids: list, confirm: bool = False):
    """
    특정 비디오들만 삭제
    
    Args:
        video_ids: 삭제할 비디오 ID 목록
        confirm: True이면 확인 없이 삭제
    """
    print(f"🗑️ 특정 비디오 삭제 ({len(video_ids)}개)")
    print("=" * 60)
    
    client = SceneGraphClient()
    
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return False
    
    # 비디오 정보 확인
    videos = client.get_videos()
    target_videos = [v for v in videos if v['video_unique_id'] in video_ids]
    
    if not target_videos:
        print("❌ 지정된 비디오를 찾을 수 없습니다.")
        return False
    
    print(f"📺 삭제할 비디오 목록:")
    for video in target_videos:
        print(f"   - {video['drama_name']} {video['episode_number']} (ID: {video['video_unique_id']})")
    
    if not confirm:
        user_input = input(f"\n정말로 이 비디오들을 삭제하시겠습니까? (yes/no): ").strip().lower()
        if user_input not in ['yes', 'y']:
            print("❌ 삭제가 취소되었습니다.")
            return False
    
    # 삭제 실행
    deleted_count = 0
    for video in target_videos:
        video_id = video['video_unique_id']
        print(f"\n삭제 중: {video['drama_name']} {video['episode_number']}")
        
        success = client.delete_video(video_id, confirm=True)
        if success:
            deleted_count += 1
            print(f"   ✅ 삭제 완료")
        else:
            print(f"   ❌ 삭제 실패")
    
    print(f"\n✅ 삭제 완료: {deleted_count}/{len(target_videos)}개")
    return deleted_count == len(target_videos)

def show_current_data():
    """현재 데이터베이스 상태 표시"""
    print("📊 현재 데이터베이스 상태")
    print("=" * 60)
    
    client = SceneGraphClient()
    
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return
    
    summary = client.get_data_summary()
    if not summary:
        print("❌ 데이터 요약을 가져올 수 없습니다.")
        return
    
    print(f"📺 비디오: {summary['total_videos']}개")
    print(f"🎭 장면: {summary['total_scenes']}개")
    print(f"👥 객체: {summary['total_objects']}개")
    print(f"🎬 이벤트: {summary['total_events']}개")
    print(f"🔗 임베딩: {summary['total_embeddings']}개")
    
    if summary['total_videos'] > 0:
        print(f"\n📋 비디오 목록:")
        for i, video in enumerate(summary['videos'], 1):
            print(f"   {i}. {video['drama_name']} {video['episode_number']} (ID: {video['video_unique_id']})")

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="데이터베이스 데이터 삭제 도구")
    parser.add_argument("--all", action="store_true", help="모든 데이터 삭제")
    parser.add_argument("--videos", nargs="+", type=int, help="삭제할 비디오 ID 목록")
    parser.add_argument("--yes", action="store_true", help="확인 없이 삭제")
    parser.add_argument("--status", action="store_true", help="현재 상태만 표시")
    
    args = parser.parse_args()
    
    if args.status:
        show_current_data()
    elif args.all:
        success = clear_all_data(confirm=args.yes)
        sys.exit(0 if success else 1)
    elif args.videos:
        success = clear_specific_videos(args.videos, confirm=args.yes)
        sys.exit(0 if success else 1)
    else:
        # 대화형 모드
        print("🗑️ 데이터베이스 삭제 도구")
        print("=" * 60)
        
        while True:
            print("\n사용 가능한 명령어:")
            print("1. 현재 상태 확인 (status)")
            print("2. 모든 데이터 삭제 (clear-all)")
            print("3. 특정 비디오 삭제 (clear-videos)")
            print("4. 종료 (quit)")
            
            choice = input("\n명령어를 선택하세요: ").strip().lower()
            
            if choice == "status":
                show_current_data()
            elif choice == "clear-all":
                clear_all_data()
            elif choice == "clear-videos":
                try:
                    video_ids = input("삭제할 비디오 ID들을 공백으로 구분하여 입력하세요: ").strip()
                    video_ids = [int(x) for x in video_ids.split() if x.isdigit()]
                    if video_ids:
                        clear_specific_videos(video_ids)
                    else:
                        print("❌ 올바른 비디오 ID를 입력해주세요.")
                except ValueError:
                    print("❌ 올바른 숫자를 입력해주세요.")
            elif choice in ["quit", "exit", "q"]:
                print("👋 프로그램을 종료합니다.")
                break
            else:
                print("❌ 잘못된 명령어입니다.")

if __name__ == "__main__":
    main()
