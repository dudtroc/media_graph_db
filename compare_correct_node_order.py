#!/usr/bin/env python3
"""
올바른 노드 순서 비교 - data2의 stores에서 node_type 추출
"""

import torch
from pathlib import Path

def compare_correct_node_order(data2_file: Path, data_backup_file: Path) -> dict:
    """올바른 방법으로 노드 순서 비교"""
    try:
        # data2 파일 로드
        data2_content = torch.load(data2_file, map_location='cpu', weights_only=False)
        data2_data = data2_content['data']
        data2_path = data2_content.get('path', '')
        
        # data2에서 node_type 추출 (stores에서)
        data2_node_types = data2_data.stores[0]['node_type'].tolist()
        
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
        
        # data2의 노드 정보 (node_type만 사용)
        data2_node_info = []
        for i, node_type in enumerate(data2_node_types):
            node_type_map = {0: 'unknown', 1: 'object', 2: 'event', 3: 'spatial'}
            node_type_name = node_type_map.get(node_type, 'unknown')
            data2_node_info.append(f"{node_type_name}_{i}")
        
        # data_backup의 노드 정보 (orig_id와 node_type 사용)
        data_backup_node_info = []
        for i, orig_id in enumerate(data_backup_orig_id):
            node_type_idx = data_backup_node_type[i] if i < len(data_backup_node_type) else 0
            node_type_map = {0: 'unknown', 1: 'object', 2: 'event', 3: 'spatial'}
            node_type_name = node_type_map.get(node_type_idx, 'unknown')
            data_backup_node_info.append(f"{node_type_name}_{orig_id}")
        
        analysis['data2_node_info'] = data2_node_info
        analysis['data_backup_node_info'] = data_backup_node_info
        analysis['node_info_match'] = data2_node_info == data_backup_node_info
        
        # node_type 순서만 비교
        data2_node_types_only = data2_node_types
        data_backup_node_types_only = data_backup_node_type.tolist() if hasattr(data_backup_node_type, 'tolist') else list(data_backup_node_type)
        
        analysis['data2_node_types'] = data2_node_types_only
        analysis['data_backup_node_types'] = data_backup_node_types_only
        analysis['node_types_match'] = data2_node_types_only == data_backup_node_types_only
        
        # 순서별 비교
        order_comparison = []
        for i in range(min(len(data2_node_info), len(data_backup_node_info))):
            order_comparison.append({
                'index': i,
                'data2': data2_node_info[i],
                'data_backup': data_backup_node_info[i],
                'data2_node_type': data2_node_types_only[i],
                'data_backup_node_type': data_backup_node_types_only[i],
                'node_type_match': data2_node_types_only[i] == data_backup_node_types_only[i],
                'full_match': data2_node_info[i] == data_backup_node_info[i]
            })
        
        analysis['order_comparison'] = order_comparison
        analysis['matching_indices'] = sum(1 for comp in order_comparison if comp['full_match'])
        analysis['node_type_matching_indices'] = sum(1 for comp in order_comparison if comp['node_type_match'])
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
    
    print("🔍 올바른 노드 순서 비교 분석")
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
        
        analysis = compare_correct_node_order(data2_file, data_backup_file)
        
        if 'error' in analysis:
            print(f"❌ 오류: {analysis['error']}")
            continue
        
        print(f"📊 임베딩 개수: data2 {analysis['data2_embedding_count']} vs data_backup {analysis['data_backup_embedding_count']}")
        print(f"📊 Path 일치: {'✅' if analysis['path_match'] else '❌'}")
        print(f"📊 Node Type 순서 일치: {'✅' if analysis['node_types_match'] else '❌'}")
        print(f"📊 전체 노드 정보 일치: {'✅' if analysis['node_info_match'] else '❌'}")
        
        if analysis['node_types_match']:
            print("✅ Node Type 순서가 완전히 일치합니다!")
            print("   → 임베딩과 노드의 매핑이 동일합니다!")
        else:
            print(f"⚠️ Node Type 순서: {analysis['node_type_matching_indices']}/{analysis['total_indices']}개 일치")
            
            # 처음 10개와 마지막 10개 비교
            print("\n🔍 처음 10개 노드 비교:")
            for i, comp in enumerate(analysis['order_comparison'][:10]):
                node_type_status = "✅" if comp['node_type_match'] else "❌"
                print(f"  {i:2d}: {node_type_status} data2={comp['data2_node_type']} | data_backup={comp['data_backup_node_type']}")
            
            if len(analysis['order_comparison']) > 10:
                print("\n🔍 마지막 10개 노드 비교:")
                for i, comp in enumerate(analysis['order_comparison'][-10:], len(analysis['order_comparison'])-10):
                    node_type_status = "✅" if comp['node_type_match'] else "❌"
                    print(f"  {i:2d}: {node_type_status} data2={comp['data2_node_type']} | data_backup={comp['data_backup_node_type']}")
        
        print(f"\n📁 Path 정보:")
        print(f"  data2: {analysis['data2_path']}")
        print(f"  data_backup: {analysis['data_backup_path']}")

if __name__ == "__main__":
    main()
