#!/usr/bin/env python3
"""
cook 검색 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scene_graph_client import SceneGraphDBClient

def debug_cook_search():
    """cook 검색 디버깅"""
    print("🔍 cook 검색 디버깅 시작")
    print("=" * 50)
    
    # 클라이언트 초기화
    client = SceneGraphDBClient()
    
    # API 서버 연결 확인
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return False
    
    print("✅ API 서버 연결 성공")
    
    # 1. "cook" 관련 이벤트 직접 검색
    print("\n1. 'cook' 관련 이벤트 직접 검색")
    print("-" * 30)
    
    try:
        # BERT 모델로 "cook" 임베딩 생성
        from sentence_transformers import SentenceTransformer
        import torch
        
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        cook_embedding = model.encode("cooking", normalize_embeddings=True, convert_to_tensor=True).float()
        
        # Event 노드에서 "cook" 검색
        cook_events = client._find_similar_nodes_with_pgvector(cook_embedding, 'event', 0.1, 10)
        
        print(f"🔍 'cook' 검색 결과: {len(cook_events)}개")
        for i, event in enumerate(cook_events[:5], 1):
            print(f"  {i}. {event['verb']} (유사도: {event['similarity']:.3f})")
            print(f"     장면: {event['drama_name']} {event['episode_number']} - {event['scene_number']}")
            print(f"     Event ID: {event['event_id']}")
            print()
    
    except Exception as e:
        print(f"❌ Event 검색 실패: {e}")
    
    # 2. "cooking" 관련 이벤트 검색
    print("\n2. 'cooking' 관련 이벤트 검색")
    print("-" * 30)
    
    try:
        cooking_embedding = model.encode("cooking", normalize_embeddings=True, convert_to_tensor=True).float()
        cooking_events = client._find_similar_nodes_with_pgvector(cooking_embedding, 'event', 0.1, 10)
        
        print(f"🔍 'cooking' 검색 결과: {len(cooking_events)}개")
        for i, event in enumerate(cooking_events[:5], 1):
            print(f"  {i}. {event['verb']} (유사도: {event['similarity']:.3f})")
            print(f"     장면: {event['drama_name']} {event['episode_number']} - {event['scene_number']}")
            print(f"     Event ID: {event['event_id']}")
            print()
    
    except Exception as e:
        print(f"❌ cooking 검색 실패: {e}")
    
    # 3. 전체 벡터 검색 테스트
    print("\n3. 전체 벡터 검색 테스트")
    print("-" * 30)
    
    try:
        result = client.vector_search("요리하는 장면을 찾아줘", top_k=3, tau=0.1)
        
        if result['success']:
            print(f"✅ 검색 성공: {len(result['search_results'])}개 결과")
            
            for i, search_result in enumerate(result['search_results'], 1):
                print(f"\n{i}. 장면: {search_result['drama_name']} {search_result['episode_number']} - {search_result['scene_number']}")
                print(f"   전체 평균 유사도: {search_result['total_avg_similarity']:.3f}")
                
                if 'satisfied_triples' in search_result:
                    for triple_result in search_result['satisfied_triples']:
                        if 'event_id' in triple_result:
                            print(f"   Event: {triple_result['verb']} (유사도: {triple_result['event_similarity']:.3f})")
                        elif 'spatial_id' in triple_result:
                            print(f"   Spatial: {triple_result['predicate']} (유사도: {triple_result['predicate_similarity']:.3f})")
        else:
            print(f"❌ 검색 실패: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ 전체 검색 실패: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 cook 검색 디버깅 완료")
    return True

if __name__ == "__main__":
    debug_cook_search()
