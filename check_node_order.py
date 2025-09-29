#!/usr/bin/env python3
"""
data2와 data_backup의 노드 정보 순서 비교
임베딩과 연결된 노드의 순서가 동일한지 확인
"""

import torch
import os
from pathlib import Path
import json

def compare_node_order(data2_file: Path, data_backup_file: Path) -> dict:
    """두 파일의 노드 정보 순서를 비교"""
    try:
        # data2 파일 로드
        data2_content = torch.load(data2_file, map_location='cpu', weights_only=False)
        data2_data = data2_content['data']
        data2_path = data2_content.get('path', '')
        
        # data_backup 파일 로드
        data_backup_content = torch.load(data_backup_file, map_location='cpu', weights_only=False)
        data_backup_z = data_backup_content['z']
        data_backup_orig_id = data_backup_content.get('orig_id', [])
        data_backup_node_type = data_backup_content.get('node_type', [])
        data_backup_path = data_backup_content.get('path', '')
        
        # 기본 정보
        analysis = {
            'file1': str(data2_file),
            'file2': str(data_backup_file),
            'data2_embedding_count': len(data2_data.x),
            'data_backup_embedding_count': len(data_backup_z),
            'path_match': data2_path == data_backup_path,
            'data2_path': data2_path,
            'data_backup_path': data_backup_path
        }
        
        # 임베딩 개수 비교
        if len(data2_data.x) != len(data_backup_z):
            analysis['error'] = f"임베딩 개수 다름: data2 {len(data2_data.x)} vs data_backup {len(data_backup_z)}"
            return analysis
        
        # data2의 노드 정보 추출 (가능한 경우)
        data2_node_info = []
        if hasattr(data2_data, 'node_offsets') and data2_data.node_offsets:
            # node_offsets에서 노드 정보 추출
            for node_type, offset in data2_data.node_offsets.items():
                data2_node_info.append(f"{node_type}_{offset}")
        else:
            # 기본적으로 임베딩 개수만큼 순서대로
            data2_node_info = [f"node_{i}" for i in range(len(data2_data.x))]
        
        # data_backup의 노드 정보 (orig_id와 node_type 사용)
        data_backup_node_info = []
        for i, orig_id in enumerate(data_backup_orig_id):
            node_type_idx = data_backup_node_type[i] if i < len(data_backup_node_type) else 0
            node_type_map = {0: 'unknown', 1: 'object', 2: 'event', 3: 'spatial'}
            node_type = node_type_map.get(node_type_idx, 'unknown')
            data_backup_node_info.append(f"{node_type}_{orig_id}")
        
        analysis['data2_node_info'] = data2_node_info
        analysis['data_backup_node_info'] = data_backup_node_info
        analysis['node_info_match'] = data2_node_info == data_backup_node_info
        
        # 순서별 비교
        order_comparison = []
        for i in range(min(len(data2_node_info), len(data_backup_node_info))):
            order_comparison.append({
                'index': i,
                'data2': data2_node_info[i],
                'data_backup': data_backup_node_info[i],
                'match': data2_node_info[i] == data_backup_node_info[i]
            })
        
        analysis['order_comparison'] = order_comparison
        analysis['matching_indices'] = sum(1 for comp in order_comparison if comp['match'])
        analysis['total_indices'] = len(order_comparison)
        
        return analysis
        
    except Exception as e:
        return {
            'file1': str(data2_file),
            'file2': str(data_backup_file),
            'error': str(e)
        }

def main():
    data2_dir = Path("/home/ktva/PROJECT/MEDIA/media-graph-db/client/data2")
    data_backup_dir = Path("/home/ktva/PROJECT/MEDIA/media-graph-db/client/data_backup")
    
    # 샘플 파일들로 테스트
    sample_files = [
        "Twenty.Five.Twenty.One_EP05_visual_44444-46903_(00_30_54-00_32_36)_meta_info.pt",
        "Our.Blues_EP13_visual_27292-30176_(00_18_58-00_20_59)_meta_info.pt",
        "The.Fiery.Priest_EP01_visual_72752-77369_(00_40_27-00_43_02)_meta_info.pt"
    ]
    
    print("🔍 노드 정보 순서 비교 분석")
    print("=" * 80)
    
    for filename in sample_files:
        print(f"\n파일: {filename}")
        print("-" * 60)
        
        data2_file = data2_dir / filename
        data_backup_file = data_backup_dir / filename
        
        if not data2_file.exists():
            print(f"❌ data2에 파일이 없습니다: {filename}")
            continue
            
        if not data_backup_file.exists():
            print(f"❌ data_backup에 파일이 없습니다: {filename}")
            continue
        
        analysis = compare_node_order(data2_file, data_backup_file)
        
        if 'error' in analysis:
            print(f"❌ 오류: {analysis['error']}")
            continue
        
        print(f"📊 임베딩 개수: data2 {analysis['data2_embedding_count']} vs data_backup {analysis['data_backup_embedding_count']}")
        print(f"📊 Path 일치: {'✅' if analysis['path_match'] else '❌'}")
        print(f"📊 노드 정보 순서 일치: {'✅' if analysis['node_info_match'] else '❌'}")
        
        if analysis['node_info_match']:
            print("✅ 모든 노드 정보가 순서대로 일치합니다!")
        else:
            print(f"⚠️ {analysis['matching_indices']}/{analysis['total_indices']}개 노드가 순서대로 일치")
            
            # 처음 10개와 마지막 10개 비교
            print("\n🔍 처음 10개 노드 비교:")
            for i, comp in enumerate(analysis['order_comparison'][:10]):
                status = "✅" if comp['match'] else "❌"
                print(f"  {i:2d}: {status} data2={comp['data2']:20s} | data_backup={comp['data_backup']}")
            
            if len(analysis['order_comparison']) > 10:
                print("\n🔍 마지막 10개 노드 비교:")
                for i, comp in enumerate(analysis['order_comparison'][-10:], len(analysis['order_comparison'])-10):
                    status = "✅" if comp['match'] else "❌"
                    print(f"  {i:2d}: {status} data2={comp['data2']:20s} | data_backup={comp['data_backup']}")
        
        print(f"\n📁 Path 정보:")
        print(f"  data2: {analysis['data2_path']}")
        print(f"  data_backup: {analysis['data_backup_path']}")

if __name__ == "__main__":
    main()
