#!/usr/bin/env python3
"""
임베딩 데이터 확인 및 테스트 스크립트
"""

import os
import json
import torch
import numpy as np
from typing import Dict, Any, List

def load_and_analyze_pt_file(pt_file_path: str):
    """PT 파일 로드 및 분석"""
    print(f"📁 PT 파일 분석: {pt_file_path}")
    print("=" * 60)
    
    try:
        # PT 파일 로드
        pt_data = torch.load(pt_file_path, map_location='cpu')
        print(f"✅ PT 파일 로드 성공")
        
        # 데이터 구조 분석
        print(f"\n📊 PT 데이터 구조:")
        print(f"  - 타입: {type(pt_data)}")
        
        if isinstance(pt_data, dict):
            print(f"  - 키들: {list(pt_data.keys())}")
            
            for key, value in pt_data.items():
                print(f"\n🔍 키 '{key}':")
                print(f"  - 타입: {type(value)}")
                
                if isinstance(value, torch.Tensor):
                    print(f"  - 텐서 형태: {value.shape}")
                    print(f"  - 데이터 타입: {value.dtype}")
                    print(f"  - 샘플 데이터 (처음 5개): {value[:5].tolist() if len(value) > 5 else value.tolist()}")
                elif isinstance(value, (list, tuple)):
                    print(f"  - 길이: {len(value)}")
                    if len(value) > 0:
                        print(f"  - 첫 번째 요소: {value[0]}")
                        print(f"  - 마지막 요소: {value[-1]}")
                else:
                    print(f"  - 값: {value}")
        
        return pt_data
        
    except Exception as e:
        print(f"❌ PT 파일 로드 실패: {e}")
        return None

def load_and_analyze_json_file(json_file_path: str):
    """JSON 파일 로드 및 분석"""
    print(f"\n📁 JSON 파일 분석: {json_file_path}")
    print("=" * 60)
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"✅ JSON 파일 로드 성공")
        
        # 장면 그래프 구조 분석
        if 'scene_graph' in json_data:
            scene_graph = json_data['scene_graph']
            print(f"\n📊 장면 그래프 구조:")
            
            # 메타 정보
            if 'meta' in scene_graph:
                meta = scene_graph['meta']
                print(f"  - 메타 정보: {meta}")
            
            # 노드들
            node_types = ['objects', 'events', 'spatial', 'temporal']
            for node_type in node_types:
                if node_type in scene_graph:
                    nodes = scene_graph[node_type]
                    print(f"  - {node_type}: {len(nodes)}개")
                    
                    # 첫 번째 노드 예시
                    if len(nodes) > 0:
                        print(f"    예시: {nodes[0]}")
        
        return json_data
        
    except Exception as e:
        print(f"❌ JSON 파일 로드 실패: {e}")
        return None

def analyze_embedding_mapping(pt_data: Dict[str, Any], json_data: Dict[str, Any]):
    """임베딩과 노드 매핑 분석"""
    print(f"\n🔗 임베딩-노드 매핑 분석")
    print("=" * 60)
    
    if not pt_data or not json_data:
        print("❌ 데이터가 없어서 매핑 분석을 할 수 없습니다.")
        return
    
    # PT 데이터에서 임베딩 정보 추출
    if 'z' in pt_data and 'orig_id' in pt_data:
        embeddings = pt_data['z']
        orig_ids = pt_data['orig_id']
        
        print(f"📊 임베딩 정보:")
        print(f"  - 임베딩 벡터 수: {len(embeddings)}")
        print(f"  - 원본 ID 수: {len(orig_ids)}")
        print(f"  - 임베딩 차원: {embeddings.shape[1] if len(embeddings.shape) > 1 else 'N/A'}")
        
        print(f"\n📋 원본 ID 목록:")
        for i, orig_id in enumerate(orig_ids):
            print(f"  {i}: {orig_id}")
        
        # JSON 데이터에서 노드 ID들 추출
        scene_graph = json_data.get('scene_graph', {})
        all_node_ids = []
        
        for node_type in ['objects', 'events', 'spatial', 'temporal']:
            if node_type in scene_graph:
                nodes = scene_graph[node_type]
                for node in nodes:
                    if 'object_id' in node:
                        all_node_ids.append(node['object_id'])
                    elif 'event_id' in node:
                        all_node_ids.append(node['event_id'])
                    elif 'spatial_id' in node:
                        all_node_ids.append(node['spatial_id'])
                    elif 'temporal_id' in node:
                        all_node_ids.append(node['temporal_id'])
        
        print(f"\n📋 JSON 노드 ID 목록:")
        for node_id in all_node_ids:
            print(f"  - {node_id}")
        
        # 매핑 확인
        print(f"\n🔍 매핑 확인:")
        matched_ids = []
        unmatched_orig_ids = []
        unmatched_node_ids = []
        
        for orig_id in orig_ids:
            if orig_id in all_node_ids:
                matched_ids.append(orig_id)
            else:
                unmatched_orig_ids.append(orig_id)
        
        for node_id in all_node_ids:
            if node_id not in orig_ids:
                unmatched_node_ids.append(node_id)
        
        print(f"  ✅ 매칭된 ID: {len(matched_ids)}개")
        if matched_ids:
            print(f"    {matched_ids}")
        
        print(f"  ❌ 매칭되지 않은 orig_id: {len(unmatched_orig_ids)}개")
        if unmatched_orig_ids:
            print(f"    {unmatched_orig_ids}")
        
        print(f"  ❌ 매칭되지 않은 node_id: {len(unmatched_node_ids)}개")
        if unmatched_node_ids:
            print(f"    {unmatched_node_ids}")
        
        return {
            'embeddings': embeddings,
            'orig_ids': orig_ids,
            'matched_ids': matched_ids,
            'unmatched_orig_ids': unmatched_orig_ids,
            'unmatched_node_ids': unmatched_node_ids
        }
    
    else:
        print("❌ PT 데이터에서 'z' 또는 'orig_id' 키를 찾을 수 없습니다.")
        return None

def test_embedding_upload():
    """임베딩 업로드 테스트"""
    print(f"\n🧪 임베딩 업로드 테스트")
    print("=" * 60)
    
    # 파일 경로
    pt_file = "data/Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.pt"
    json_file = "data/Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json"
    
    if not os.path.exists(pt_file):
        print(f"❌ PT 파일을 찾을 수 없습니다: {pt_file}")
        return
    
    if not os.path.exists(json_file):
        print(f"❌ JSON 파일을 찾을 수 없습니다: {json_file}")
        return
    
    # 데이터 로드 및 분석
    pt_data = load_and_analyze_pt_file(pt_file)
    json_data = load_and_analyze_json_file(json_file)
    
    # 매핑 분석
    mapping_result = analyze_embedding_mapping(pt_data, json_data)
    
    if mapping_result:
        print(f"\n💡 권장사항:")
        if mapping_result['unmatched_orig_ids'] or mapping_result['unmatched_node_ids']:
            print(f"  - 일부 노드 ID가 매칭되지 않습니다.")
            print(f"  - 임베딩 데이터와 JSON 데이터의 ID 체계를 확인해주세요.")
        else:
            print(f"  - 모든 노드 ID가 정상적으로 매칭됩니다.")
            print(f"  - 임베딩 데이터를 데이터베이스에 저장할 수 있습니다.")

def main():
    """메인 함수"""
    print("🔍 임베딩 데이터 분석 도구")
    print("=" * 60)
    
    test_embedding_upload()

if __name__ == "__main__":
    main()
