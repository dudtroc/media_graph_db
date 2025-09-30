#!/usr/bin/env python3
"""
cooking vs cook 임베딩 유사도 비교
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scene_graph_client import SceneGraphDBClient
import torch
from sentence_transformers import SentenceTransformer
import numpy as np

def debug_cooking_embedding():
    """cooking vs cook 임베딩 유사도 비교"""
    print("🔍 Cooking vs Cook 임베딩 유사도 비교")
    print("=" * 50)
    
    # BERT 모델 로드
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    # 임베딩 생성
    cook_embedding = model.encode("cook", normalize_embeddings=True, convert_to_tensor=True).float()
    cooking_embedding = model.encode("cooking", normalize_embeddings=True, convert_to_tensor=True).float()
    
    # 코사인 유사도 계산
    similarity = torch.cosine_similarity(cook_embedding, cooking_embedding, dim=0)
    print(f"📊 'cook' vs 'cooking' 임베딩 유사도: {similarity:.4f}")
    
    # 클라이언트 초기화
    client = SceneGraphDBClient()
    
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return
    
    print("\n1. 'cook' 직접 검색 (상위 5개)")
    print("-" * 30)
    cook_events = client._find_similar_nodes_with_pgvector(cook_embedding, 'event', 0.1, 5)
    for i, event in enumerate(cook_events, 1):
        print(f"  {i}. {event['verb']} (유사도: {event['similarity']:.3f})")
    
    print("\n2. 'cooking' 직접 검색 (상위 5개)")
    print("-" * 30)
    cooking_events = client._find_similar_nodes_with_pgvector(cooking_embedding, 'event', 0.1, 5)
    for i, event in enumerate(cooking_events, 1):
        print(f"  {i}. {event['verb']} (유사도: {event['similarity']:.3f})")
    
    print("\n3. 'cooking'으로 검색했을 때 'cook' 이벤트가 몇 번째에 나오는지 확인")
    print("-" * 30)
    for i, event in enumerate(cooking_events, 1):
        if event['verb'] == 'cook':
            print(f"  ✅ 'cook' 이벤트가 {i}번째에 발견됨 (유사도: {event['similarity']:.3f})")
            break
    else:
        print("  ❌ 'cook' 이벤트를 찾을 수 없음")
    
    print("\n4. 전체 벡터 검색에서 사용되는 임베딩 확인")
    print("-" * 30)
    
    # Triple 변환 과정 시뮬레이션
    
    # 질문을 triple로 변환하는 과정
    query = "요리하는 장면을 찾아줘"
    print(f"질문: {query}")
    
    # LLM 응답 시뮬레이션 (실제와 동일)
    triples = [["person:person", "cooking", None]]
    print(f"변환된 triples: {triples}")
    
    # 각 요소별 임베딩 생성
    s_emb = None  # Subject가 None이므로
    v_emb = model.encode("cooking", normalize_embeddings=True, convert_to_tensor=True).float()
    o_emb = None  # Object가 None이므로
    
    print(f"Subject 임베딩: {s_emb}")
    print(f"Verb 임베딩: {v_emb.shape if v_emb is not None else 'None'}")
    print(f"Object 임베딩: {o_emb}")
    
    # Verb 임베딩으로 직접 검색
    print(f"\n5. 'cooking' 임베딩으로 직접 검색 (상위 10개)")
    print("-" * 30)
    verb_events = client._find_similar_nodes_with_pgvector(v_emb, 'event', 0.1, 10)
    for i, event in enumerate(verb_events, 1):
        print(f"  {i}. {event['verb']} (유사도: {event['similarity']:.3f})")
    
    print("\n" + "=" * 50)
    print("🏁 임베딩 분석 완료")

if __name__ == "__main__":
    debug_cooking_embedding()
