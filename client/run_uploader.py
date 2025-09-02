#!/usr/bin/env python3
"""
장면 그래프 업로더 실행 스크립트
"""

import os
import sys
from scene_graph_uploader import SceneGraphUploader

def main():
    """메인 실행 함수"""
    print("🎬 Scene Graph Database 업로더 실행")
    print("=" * 50)
    
    # API 서버 상태 확인
    uploader = SceneGraphUploader()
    
    try:
        import requests
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
