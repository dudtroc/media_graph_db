#!/usr/bin/env python3
"""
data 폴더의 장면그래프 JSON과 PT 파일을 업로드하고 임베딩 저장을 테스트하는 스크립트
"""

import os
import sys
import json
import torch
import numpy as np
from pathlib import Path
from scene_graph_client import SceneGraphDBClient

def check_pt_file_structure(pt_file_path: str) -> dict:
    """PT 파일의 구조를 확인하고 임베딩 정보를 반환"""
    print(f"🔍 PT 파일 구조 확인: {os.path.basename(pt_file_path)}")
    
    try:
        # PT 파일 로드
        pt_data = torch.load(pt_file_path, map_location='cpu')
        
        print(f"📊 PT 파일 키들: {list(pt_data.keys())}")
        
        # 임베딩 데이터 확인
        if 'z' in pt_data:
            embeddings = pt_data['z']
            if hasattr(embeddings, 'shape'):
                print(f"✅ 임베딩 벡터 차원: {embeddings.shape}")
                print(f"✅ 임베딩 개수: {embeddings.shape[0] if len(embeddings.shape) > 0 else 1}")
            else:
                print(f"✅ 임베딩 타입: {type(embeddings)}")
                print(f"✅ 임베딩 길이: {len(embeddings) if hasattr(embeddings, '__len__') else 'N/A'}")
        
        # 노드 타입 정보 확인
        if 'node_type' in pt_data:
            node_types = pt_data['node_type']
            if hasattr(node_types, 'shape'):
                print(f"✅ 노드 타입 차원: {node_types.shape}")
            else:
                print(f"✅ 노드 타입 타입: {type(node_types)}")
                print(f"✅ 노드 타입 길이: {len(node_types) if hasattr(node_types, '__len__') else 'N/A'}")
        
        return {
            'success': True,
            'data': pt_data,
            'embedding_count': embeddings.shape[0] if 'z' in pt_data and hasattr(embeddings, 'shape') else 0,
            'embedding_dim': embeddings.shape[1] if 'z' in pt_data and len(embeddings.shape) > 1 else 0
        }
        
    except Exception as e:
        print(f"❌ PT 파일 로드 실패: {e}")
        return {'success': False, 'error': str(e)}

def check_if_scene_exists(client: SceneGraphDBClient, drama_name: str, episode_number: str, start_frame: int, end_frame: int) -> bool:
    """해당 장면이 이미 존재하는지 확인"""
    try:
        # 비디오 목록에서 해당 드라마/에피소드 찾기
        videos = client.get_videos()
        target_video = None
        
        for video in videos:
            if video['drama_name'] == drama_name and video['episode_number'] == episode_number:
                target_video = video
                break
        
        if not target_video:
            return False
        
        # 해당 비디오의 장면 목록 확인
        scenes = client.get_scenes(target_video['id'])
        for scene in scenes:
            if scene['start_frame'] == start_frame and scene['end_frame'] == end_frame:
                print(f"⚠️ 이미 존재하는 장면: {drama_name} {episode_number} 프레임 {start_frame}-{end_frame}")
                return True
        
        return False
    except Exception as e:
        print(f"⚠️ 중복 체크 실패: {e}")
        return False

def test_single_file_upload(client: SceneGraphDBClient, json_file: str, pt_file: str) -> tuple[bool, str]:
    """단일 파일 업로드 테스트"""
    print(f"\n🚀 단일 파일 업로드 테스트")
    print(f"📄 JSON: {os.path.basename(json_file)}")
    print(f"📄 PT: {os.path.basename(pt_file)}")
    print("-" * 50)
    
    # 1. PT 파일 구조 확인
    pt_info = check_pt_file_structure(pt_file)
    if not pt_info['success']:
        print(f"❌ PT 파일 확인 실패: {pt_info['error']}")
        return False
    
    print(f"✅ PT 파일 확인 완료 - 임베딩 {pt_info['embedding_count']}개, 차원 {pt_info['embedding_dim']}")
    
    # 2. 파일명에서 드라마/에피소드/프레임 정보 추출
    try:
        filename = os.path.basename(json_file)
        import re
        match = re.match(r'(.+)_(.+)_visual_(\d+)-(\d+)_.*_meta_info\.json', filename)
        if match:
            drama_name, episode_number, start_frame, end_frame = match.groups()
            start_frame, end_frame = int(start_frame), int(end_frame)
            
            # 3. 중복 체크
            if check_if_scene_exists(client, drama_name, episode_number, start_frame, end_frame):
                print(f"⏭️ 중복된 장면이므로 스킵합니다.")
                return True, "skipped"
        else:
            print(f"⚠️ 파일명 파싱 실패, 중복 체크를 건너뜁니다.")
    except Exception as e:
        print(f"⚠️ 중복 체크 중 오류: {e}")
    
    # 4. JSON 파일 업로드 (PT 파일은 자동으로 찾아서 처리됨)
    print(f"\n📤 JSON 파일 업로드 시작...")
    success = client.upload_scene_graph(json_file)
    
    if success:
        print(f"✅ 업로드 성공!")
        return True, "success"
    else:
        print(f"❌ 업로드 실패!")
        return False, "failed"

def verify_uploaded_data(client: SceneGraphDBClient, expected_drama: str, expected_episode: str) -> dict:
    """업로드된 데이터 검증"""
    print(f"\n🔍 업로드된 데이터 검증")
    print("-" * 30)
    
    try:
        # 1. 비디오 목록 확인
        videos = client.get_videos()
        print(f"📺 저장된 비디오 수: {len(videos)}")
        
        target_video = None
        for video in videos:
            if video['drama_name'] == expected_drama and video['episode_number'] == expected_episode:
                target_video = video
                break
        
        if not target_video:
            print(f"❌ 대상 비디오를 찾을 수 없습니다: {expected_drama} {expected_episode}")
            return {'success': False, 'error': 'Video not found'}
        
        print(f"✅ 대상 비디오 발견: {target_video['drama_name']} {target_video['episode_number']} (ID: {target_video['id']})")
        
        # 2. 장면 목록 확인
        scenes = client.get_scenes(target_video['id'])
        print(f"🎭 저장된 장면 수: {len(scenes)}")
        
        if not scenes:
            print(f"❌ 장면이 없습니다.")
            return {'success': False, 'error': 'No scenes found'}
        
        # 3. 첫 번째 장면의 상세 정보 확인
        scene = scenes[0]
        print(f"🎬 첫 번째 장면 ID: {scene['id']}")
        
        # 4. 장면 그래프 정보 조회
        scene_graph = client.get_scene_graph(scene['id'])
        if not scene_graph:
            print(f"❌ 장면 그래프 정보를 가져올 수 없습니다.")
            return {'success': False, 'error': 'Scene graph not found'}
        
        # 5. 노드 정보 확인
        objects = scene_graph.get('objects', [])
        events = scene_graph.get('events', [])
        spatial = scene_graph.get('spatial', [])
        temporal = scene_graph.get('temporal', [])
        
        print(f"👥 객체 수: {len(objects)}")
        print(f"🎬 이벤트 수: {len(events)}")
        print(f"📍 공간관계 수: {len(spatial)}")
        print(f"⏰ 시간관계 수: {len(temporal)}")
        
        # 6. 임베딩 정보 확인
        embeddings = client.get_scene_embeddings(scene['id'])
        print(f"🧠 임베딩 수: {len(embeddings)}")
        
        if embeddings:
            print(f"✅ 임베딩 데이터가 성공적으로 저장되었습니다!")
            for i, emb in enumerate(embeddings[:3]):  # 처음 3개만 출력
                embedding_data = emb.get('embedding', [])
                # embedding이 문자열인 경우 파싱
                if isinstance(embedding_data, str):
                    try:
                        import json
                        embedding_list = json.loads(embedding_data)
                        dimension = len(embedding_list)
                    except:
                        dimension = "파싱 실패"
                else:
                    dimension = len(embedding_data)
                print(f"  - 임베딩 {i+1}: 노드 ID {emb.get('node_id')}, 차원 {dimension}")
        else:
            print(f"⚠️ 임베딩 데이터가 없습니다.")
        
        return {
            'success': True,
            'video_id': target_video['id'],
            'scene_id': scene['id'],
            'objects_count': len(objects),
            'events_count': len(events),
            'spatial_count': len(spatial),
            'temporal_count': len(temporal),
            'embeddings_count': len(embeddings)
        }
        
    except Exception as e:
        print(f"❌ 데이터 검증 실패: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """메인 실행 함수"""
    print("🎬 data 폴더 장면그래프 업로드 테스트")
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
        print("💡 서버가 실행 중인지 확인해주세요.")
        return
    
    # data 폴더 경로
    data_dir = Path("data")
    if not data_dir.exists():
        print(f"❌ data 폴더를 찾을 수 없습니다: {data_dir.absolute()}")
        return
    
    # JSON 파일들 찾기
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print(f"❌ data 폴더에서 JSON 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 발견된 JSON 파일: {len(json_files)}개")
    
    # 각 JSON 파일에 대해 테스트
    success_count = 0
    skipped_count = 0
    total_count = len(json_files)
    
    for i, json_file in enumerate(json_files, 1):
        print(f"\n{'='*60}")
        print(f"📄 [{i}/{total_count}] 테스트: {json_file.name}")
        print(f"{'='*60}")
        
        # 대응하는 PT 파일 찾기
        pt_file = json_file.with_suffix('.pt')
        if not pt_file.exists():
            print(f"❌ 대응하는 PT 파일을 찾을 수 없습니다: {pt_file.name}")
            continue
        
        # 파일명에서 드라마와 에피소드 정보 추출
        try:
            # 파일명 파싱 (예: Hospital.Playlist_EP01_visual_181-455_(00_00_06-00_00_15)_meta_info.json)
            filename = json_file.stem
            parts = filename.split('_')
            drama_name = parts[0]  # Hospital.Playlist
            episode_number = parts[1]  # EP01
            
            print(f"📺 드라마: {drama_name}, 에피소드: {episode_number}")
            
        except Exception as e:
            print(f"⚠️ 파일명 파싱 실패: {e}")
            drama_name = "Unknown"
            episode_number = "Unknown"
        
        # 단일 파일 업로드 테스트
        upload_success, status = test_single_file_upload(client, str(json_file), str(pt_file))
        
        if upload_success:
            # 중복 체크로 스킵된 경우인지 확인
            if status == "skipped":
                print(f"⏭️ [{i}/{total_count}] 중복으로 스킵됨")
                skipped_count += 1
            else:
                # 업로드된 데이터 검증
                verification = verify_uploaded_data(client, drama_name, episode_number)
                
                if verification['success']:
                    print(f"✅ [{i}/{total_count}] 테스트 성공!")
                    print(f"   - 비디오 ID: {verification['video_id']}")
                    print(f"   - 장면 ID: {verification['scene_id']}")
                    print(f"   - 객체: {verification['objects_count']}개")
                    print(f"   - 이벤트: {verification['events_count']}개")
                    print(f"   - 공간관계: {verification['spatial_count']}개")
                    print(f"   - 시간관계: {verification['temporal_count']}개")
                    print(f"   - 임베딩: {verification['embeddings_count']}개")
                    success_count += 1
                else:
                    print(f"❌ [{i}/{total_count}] 데이터 검증 실패: {verification['error']}")
        else:
            print(f"❌ [{i}/{total_count}] 업로드 실패")
    
    # 최종 결과 요약
    print(f"\n{'='*60}")
    print(f"📊 테스트 결과 요약")
    print(f"{'='*60}")
    print(f"✅ 성공: {success_count}개")
    print(f"⏭️ 스킵: {skipped_count}개 (중복)")
    print(f"❌ 실패: {total_count - success_count - skipped_count}개")
    print(f"📁 총 처리: {total_count}개")
    
    if success_count > 0:
        print(f"\n🎉 {success_count}개 파일이 성공적으로 업로드되었습니다!")
        
        # 전체 데이터 요약
        print(f"\n📊 전체 데이터베이스 상태:")
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
        print(f"\n💥 모든 파일 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
