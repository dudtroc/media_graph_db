#!/usr/bin/env python3
"""
PT 파일의 구조를 분석하여 노드 타입별 임베딩 정보가 어떻게 구분되어 있는지 확인
"""

import os
import torch
import numpy as np
from pathlib import Path

def analyze_pt_file(pt_file_path: str):
    """PT 파일의 구조를 상세히 분석"""
    print(f"🔍 PT 파일 분석: {os.path.basename(pt_file_path)}")
    print("=" * 60)
    
    try:
        # PT 파일 로드
        pt_data = torch.load(pt_file_path, map_location='cpu')
        
        print(f"📊 PT 파일 키들: {list(pt_data.keys())}")
        print()
        
        # 각 키별 상세 분석
        for key, value in pt_data.items():
            print(f"🔑 키: {key}")
            if hasattr(value, 'shape'):
                print(f"   - 타입: {type(value)}")
                print(f"   - 형태: {value.shape}")
                if key == 'z':
                    print(f"   - 임베딩 벡터 (첫 3개):")
                    for i in range(min(3, value.shape[0])):
                        print(f"     [{i}]: {value[i][:5].tolist()}... (384차원)")
                elif key == 'node_type':
                    print(f"   - 노드 타입 값들: {value.tolist()}")
                    unique_types = torch.unique(value)
                    print(f"   - 고유 노드 타입: {unique_types.tolist()}")
                    for node_type in unique_types:
                        count = (value == node_type).sum().item()
                        print(f"     - 타입 {node_type}: {count}개")
                elif key == 'orig_id':
                    print(f"   - orig_id 값들: {value.tolist()}")
                    print(f"   - orig_id 범위: {value.min().item()} ~ {value.max().item()}")
                    print(f"   - 고유 orig_id: {len(torch.unique(value))}개")
            else:
                print(f"   - 타입: {type(value)}")
                print(f"   - 값: {value}")
            print()
        
        # 노드 타입별 orig_id 분석
        if 'node_type' in pt_data and 'orig_id' in pt_data:
            print("📋 노드 타입별 orig_id 분석:")
            print("-" * 40)
            
            node_types = pt_data['node_type']
            orig_ids = pt_data['orig_id']
            
            for node_type in torch.unique(node_types):
                mask = node_types == node_type
                type_orig_ids = orig_ids[mask]
                
                print(f"🔸 노드 타입 {node_type}:")
                print(f"   - 개수: {len(type_orig_ids)}")
                print(f"   - orig_id 범위: {type_orig_ids.min().item()} ~ {type_orig_ids.max().item()}")
                print(f"   - orig_id 값들: {type_orig_ids.tolist()}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ PT 파일 분석 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🔍 PT 파일 구조 분석")
    print("=" * 60)
    
    data2_path = Path("data2")
    if not data2_path.exists():
        print("❌ data2 폴더를 찾을 수 없습니다.")
        return
    
    # PT 파일들 찾기
    pt_files = list(data2_path.glob("*.pt"))
    if not pt_files:
        print("❌ PT 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 발견된 PT 파일: {len(pt_files)}개")
    print()
    
    # 각 PT 파일 분석
    for i, pt_file in enumerate(pt_files, 1):
        print(f"📄 [{i}/{len(pt_files)}] {pt_file.name}")
        analyze_pt_file(str(pt_file))
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()
