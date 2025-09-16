#!/usr/bin/env python3
"""
새로운 SceneGraphClient 인터페이스 테스트
직접 데이터를 입력받아 업로드하는 방식 테스트
"""

import json
import numpy as np
from scene_graph_client import SceneGraphClient

def create_sample_data():
    """샘플 데이터 생성"""
    
    # 1. 장면그래프 데이터 (JSON 형식)
    scene_data = {
        "scene_graph": {
            "meta": {
                "scene_place": "hospital_room",
                "scene_time": "day",
                "scene_atmosphere": "tense_and_serious"
            },
            "objects": [
                {
                    "object_id": 1001,
                    "super_type": "person",
                    "type of": "physician",
                    "label": "physician",
                    "attributes": {
                        "emotion": "focused"
                    }
                },
                {
                    "object_id": 1002,
                    "super_type": "person", 
                    "type of": "physician",
                    "label": "physician",
                    "attributes": {
                        "emotion": "concentrated"
                    }
                },
                {
                    "object_id": 1003,
                    "super_type": "clothing",
                    "type of": "hanbok",
                    "label": "hanbok"
                },
                {
                    "object_id": 1004,
                    "super_type": "accessory",
                    "type of": "hat",
                    "label": "hat"
                },
                {
                    "object_id": 1005,
                    "super_type": "clothing",
                    "type of": "hanbok", 
                    "label": "hanbok"
                },
                {
                    "object_id": 1006,
                    "super_type": "furniture",
                    "type of": "lamp",
                    "label": "lamp"
                },
                {
                    "object_id": 1007,
                    "super_type": "furniture",
                    "type of": "screen",
                    "label": "screen"
                },
                {
                    "object_id": 1008,
                    "super_type": "tool",
                    "type of": "scale",
                    "label": "scale"
                },
                {
                    "object_id": 1009,
                    "super_type": "tool",
                    "type of": "acupuncture_needles",
                    "label": "acupuncture_needles"
                },
                {
                    "object_id": 1010,
                    "super_type": "container",
                    "type of": "bowl",
                    "label": "bowl"
                }
            ],
            "events": [
                {
                    "event_id": 3001,
                    "subject": 1001,
                    "verb": "walk",
                    "attribute": "slowly"
                },
                {
                    "event_id": 3002,
                    "subject": 1002,
                    "verb": "walk",
                    "attribute": "carefully"
                },
                {
                    "event_id": 3003,
                    "subject": 1001,
                    "verb": "enter",
                    "attribute": "quietly"
                },
                {
                    "event_id": 3004,
                    "subject": 1001,
                    "verb": "kneel",
                    "attribute": "respectfully"
                },
                {
                    "event_id": 3005,
                    "subject": 1002,
                    "verb": "stand",
                    "attribute": "straight"
                },
                {
                    "event_id": 3006,
                    "subject": 1001,
                    "verb": "measure",
                    "attribute": "precisely"
                },
                {
                    "event_id": 3007,
                    "subject": 1002,
                    "verb": "kneel",
                    "attribute": "patiently"
                },
                {
                    "event_id": 3008,
                    "subject": 1001,
                    "verb": "peek",
                    "attribute": "cautiously"
                },
                {
                    "event_id": 3009,
                    "subject": 1002,
                    "verb": "look_up",
                    "attribute": "expectantly"
                }
            ],
            "spatial": [
                {
                    "spatial_id": 20000,
                    "subject": 1001,
                    "predicate": "near",
                    "object": 1006
                },
                {
                    "spatial_id": 20001,
                    "subject": 1002,
                    "predicate": "behind",
                    "object": 1001
                },
                {
                    "spatial_id": 20002,
                    "subject": 1007,
                    "predicate": "above",
                    "object": 1001
                },
                {
                    "spatial_id": 20003,
                    "subject": 1008,
                    "predicate": "beside",
                    "object": 1001
                },
                {
                    "spatial_id": 20004,
                    "subject": 1009,
                    "predicate": "inside",
                    "object": 1010
                }
            ],
            "temporal": [
                {
                    "temporal_id": 40001,
                    "subject": 3001,
                    "predicate": "before",
                    "object": 3003
                },
                {
                    "temporal_id": 40002,
                    "subject": 3003,
                    "predicate": "before",
                    "object": 3004
                },
                {
                    "temporal_id": 40003,
                    "subject": 3004,
                    "predicate": "before",
                    "object": 3006
                }
            ]
        }
    }
    
    # 2. 임베딩 정보
    # 노드 정보 (scene 제외한 모든 노드)
    node_info = [
        {'node_type': 'scene', 'node_id': 50000, 'node_label': 'scene', 'type_name': 'scene'},
        {'node_type': 'object', 'node_id': 1001, 'node_label': 'physician', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1002, 'node_label': 'physician', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1003, 'node_label': 'hanbok', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1004, 'node_label': 'hat', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1005, 'node_label': 'hanbok', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1006, 'node_label': 'lamp', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1007, 'node_label': 'screen', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1008, 'node_label': 'scale', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1009, 'node_label': 'acupuncture_needles', 'type_name': 'object'},
        {'node_type': 'object', 'node_id': 1010, 'node_label': 'bowl', 'type_name': 'object'},
        {'node_type': 'event', 'node_id': 3001, 'node_label': 'walk', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3002, 'node_label': 'walk', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3003, 'node_label': 'enter', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3004, 'node_label': 'kneel', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3005, 'node_label': 'stand', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3006, 'node_label': 'measure', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3007, 'node_label': 'kneel', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3008, 'node_label': 'peek', 'type_name': 'event'},
        {'node_type': 'event', 'node_id': 3009, 'node_label': 'look_up', 'type_name': 'event'},
        {'node_type': 'spatial', 'node_id': 20000, 'node_label': 'spatial', 'type_name': 'spatial'},
        {'node_type': 'spatial', 'node_id': 20001, 'node_label': 'spatial', 'type_name': 'spatial'},
        {'node_type': 'spatial', 'node_id': 20002, 'node_label': 'spatial', 'type_name': 'spatial'},
        {'node_type': 'spatial', 'node_id': 20003, 'node_label': 'spatial', 'type_name': 'spatial'},
        {'node_type': 'spatial', 'node_id': 20004, 'node_label': 'spatial', 'type_name': 'spatial'}
    ]
    
    # 임베딩 벡터들 (384차원, 랜덤 생성)
    node_embeddings = []
    for i in range(len(node_info)):
        # 384차원 랜덤 벡터 생성
        embedding = np.random.randn(384).tolist()
        node_embeddings.append(embedding)
    
    embedding_info = {
        'node_info': node_info,
        'node_embeddings': node_embeddings
    }
    
    return scene_data, embedding_info

def test_new_interface():
    """새로운 인터페이스 테스트"""
    print("🧪 새로운 SceneGraphClient 인터페이스 테스트")
    print("=" * 60)
    
    # 클라이언트 초기화
    client = SceneGraphDBClient()
    
    # 헬스 체크
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return False
    
    # 샘플 데이터 생성
    scene_data, embedding_info = create_sample_data()
    
    # 업로드 파라미터
    video_unique_id = 12345
    drama_name = "Hospital.Playlist"
    episode_number = "EP01"
    start_frame = 181
    end_frame = 455
    
    print(f"📺 비디오: {drama_name} {episode_number}")
    print(f"🎭 장면: 프레임 {start_frame}-{end_frame}")
    print(f"🔗 노드 수: {len(embedding_info['node_info'])}개")
    print(f"🧠 임베딩 수: {len(embedding_info['node_embeddings'])}개")
    print()
    
    # 업로드 실행
    success = client.upload_scene_graph_with_pt(
        scene_data=scene_data,
        embedding_info=embedding_info,
        video_unique_id=video_unique_id,
        drama_name=drama_name,
        episode_number=episode_number,
        start_frame=start_frame,
        end_frame=end_frame
    )
    
    if success:
        print("\n✅ 업로드 성공!")
        
        # 저장된 데이터 확인
        print("\n🔍 저장된 데이터 확인:")
        videos = client.get_videos()
        print(f"📺 총 비디오 수: {len(videos)}")
        
        for video in videos:
            if video['drama_name'] == drama_name:
                print(f"  - {video['drama_name']} {video['episode_number']} (ID: {video['id']})")
                
                # 장면 정보 확인
                scenes = client.get_scenes(video['id'])
                print(f"    장면 수: {len(scenes)}")
                
                for scene in scenes:
                    print(f"      - 장면 {scene['scene_number']} (ID: {scene['id']})")
                    
                    # 노드 정보 확인
                    objects = client.get_scene_objects(scene['id'])
                    events = client.get_scene_events(scene['id'])
                    spatial = client.get_scene_spatial_relations(scene['id'])
                    temporal = client.get_scene_temporal_relations(scene['id'])
                    embeddings = client.get_scene_embeddings(scene['id'])
                    
                    print(f"        객체: {len(objects)}개")
                    print(f"        이벤트: {len(events)}개")
                    print(f"        공간관계: {len(spatial)}개")
                    print(f"        시간관계: {len(temporal)}개")
                    print(f"        임베딩: {len(embeddings)}개")
        
        return True
    else:
        print("\n❌ 업로드 실패!")
        return False

if __name__ == "__main__":
    test_new_interface()
