#!/usr/bin/env python3
"""
단일 파일 업로드 테스트 스크립트
"""

import os
import sys
from pathlib import Path
from scene_graph_client import SceneGraphDBClient

def test_single_upload():
    """단일 파일 업로드 테스트"""
    if len(sys.argv) < 2:
        print("사용법: python test_single_upload.py \"json_file_path\"")
        return
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        return
    
    print(f"🎬 단일 파일 업로드 테스트: {json_file}")
    print("=" * 60)
    
    # 클라이언트 초기화
    try:
        client = SceneGraphDBClient()
        print("✅ SceneGraphDBClient 초기화 완료")
    except Exception as e:
        print(f"❌ 클라이언트 초기화 실패: {e}")
        return
    
    # API 서버 연결 확인
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return
    
    # 파일 업로드
    print(f"\n🚀 업로드 시작: {json_file}")
    success = client.upload_scene_graph(json_file)
    
    if success:
        print(f"✅ 업로드 성공!")
        
        # 업로드된 데이터 확인
        print(f"\n📊 업로드된 데이터 확인:")
        try:
            summary = client.get_data_summary()
            print(f"  - 총 비디오: {summary['total_videos']}개")
            print(f"  - 총 장면: {summary['total_scenes']}개")
            print(f"  - 총 객체: {summary['total_objects']}개")
            print(f"  - 총 이벤트: {summary['total_events']}개")
            print(f"  - 총 임베딩: {summary['total_embeddings']}개")
        except Exception as e:
            print(f"  ⚠️ 데이터 요약 조회 실패: {e}")
    else:
        print(f"❌ 업로드 실패!")

if __name__ == "__main__":
    test_single_upload()
