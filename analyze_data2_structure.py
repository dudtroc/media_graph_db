#!/usr/bin/env python3
"""
data2의 Data 객체 구조를 상세히 분석
"""

import torch
from pathlib import Path

def analyze_data2_structure(data2_file: Path) -> dict:
    """data2 파일의 Data 객체 구조를 분석"""
    try:
        data2_content = torch.load(data2_file, map_location='cpu', weights_only=False)
        data_obj = data2_content['data']
        
        analysis = {
            'file': str(data2_file),
            'data_type': type(data_obj).__name__,
            'attributes': {}
        }
        
        # Data 객체의 모든 속성 분석
        for attr_name in dir(data_obj):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(data_obj, attr_name)
                    if not callable(attr_value):
                        attr_info = {
                            'type': type(attr_value).__name__,
                            'value': None
                        }
                        
                        if isinstance(attr_value, torch.Tensor):
                            attr_info['shape'] = list(attr_value.shape)
                            attr_info['dtype'] = str(attr_value.dtype)
                            if attr_value.numel() < 20:  # 작은 텐서만 값 출력
                                attr_info['value'] = attr_value.tolist()
                        elif isinstance(attr_value, (list, tuple)) and len(attr_value) < 20:
                            attr_info['value'] = list(attr_value)
                        elif isinstance(attr_value, dict) and len(attr_value) < 10:
                            attr_info['value'] = dict(attr_value)
                        elif hasattr(attr_value, '__len__') and not isinstance(attr_value, str):
                            attr_info['length'] = len(attr_value)
                        
                        analysis['attributes'][attr_name] = attr_info
                except:
                    pass
        
        return analysis
        
    except Exception as e:
        return {'file': str(data2_file), 'error': str(e)}

def main():
    data2_dir = Path("/home/ktva/PROJECT/MEDIA/media-graph-db/client/data2")
    
    # 샘플 파일 분석
    filename = "Twenty.Five.Twenty.One_EP05_visual_44444-46903_(00_30_54-00_32_36)_meta_info.pt"
    data2_file = data2_dir / filename
    
    print("🔍 data2 Data 객체 구조 분석")
    print("=" * 80)
    
    analysis = analyze_data2_structure(data2_file)
    
    if 'error' in analysis:
        print(f"❌ 오류: {analysis['error']}")
        return
    
    print(f"📁 파일: {filename}")
    print(f"📊 Data 타입: {analysis['data_type']}")
    print()
    
    print("🔍 주요 속성들:")
    important_attrs = ['x', 'edge_index', 'node_offsets', 'node_stores', 'edge_stores', 'stores']
    
    for attr_name in important_attrs:
        if attr_name in analysis['attributes']:
            attr_info = analysis['attributes'][attr_name]
            print(f"\n📌 {attr_name}:")
            print(f"  - 타입: {attr_info['type']}")
            if 'shape' in attr_info:
                print(f"  - Shape: {attr_info['shape']}")
            if 'dtype' in attr_info:
                print(f"  - Dtype: {attr_info['dtype']}")
            if 'length' in attr_info:
                print(f"  - 길이: {attr_info['length']}")
            if 'value' is not None and attr_info['value'] is not None:
                print(f"  - 값: {attr_info['value']}")
    
    # stores 정보 상세 분석
    if 'stores' in analysis['attributes']:
        stores = analysis['attributes']['stores']
        print(f"\n🔍 stores 상세 정보:")
        if stores['value']:
            for i, store in enumerate(stores['value']):
                print(f"  Store {i}: {type(store).__name__}")
                if hasattr(store, 'keys'):
                    print(f"    키들: {list(store.keys())}")
                if hasattr(store, 'x') and hasattr(store.x, 'shape'):
                    print(f"    x shape: {store.x.shape}")
                if hasattr(store, 'node_type') and hasattr(store.node_type, 'shape'):
                    print(f"    node_type shape: {store.node_type.shape}")
                if hasattr(store, 'orig_id') and hasattr(store.orig_id, 'shape'):
                    print(f"    orig_id shape: {store.orig_id.shape}")

if __name__ == "__main__":
    main()
