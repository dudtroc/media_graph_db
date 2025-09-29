#!/usr/bin/env python3
"""
R-GCN 그래프 임베딩을 활용한 벡터 검색 테스트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from scene_graph_client import SceneGraphDBClient


def test_rgcn_search():
    """R-GCN 검색 테스트"""
    print("🧪 R-GCN 그래프 임베딩 검색 테스트 시작")
    
    # 클라이언트 초기화
    client = SceneGraphDBClient()
    
    # 서버 연결 확인
    if not client.health_check():
        print("❌ 서버 연결 실패")
        return
    
    print("✅ 서버 연결 성공")
    
    # 테스트 쿼리들
    test_queries = [
        "사람이 걷는 장면을 찾아줘",
        "차를 운전하는 장면은?",
        "음식을 먹는 사람이 있는가?",
        "대화하는 장면을 보여줘"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"테스트 {i}: {query}")
        print('='*50)
        
        # R-GCN 사용 검색
        print("\n🔍 R-GCN 검색 결과:")
        try:
            rgcn_results = client.vector_search(query, top_k=3, tau=0.3, use_rgcn=True)
            if rgcn_results['success']:
                print(f"✅ R-GCN 검색 성공: {len(rgcn_results['search_results'])}개 결과")
                client.print_search_results(rgcn_results['search_results'], rgcn_results['triples'])
            else:
                print(f"❌ R-GCN 검색 실패: {rgcn_results.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ R-GCN 검색 예외: {e}")
        
        # SBERT만 사용 검색 (비교용)
        print("\n🔍 SBERT 검색 결과:")
        try:
            sbert_results = client.vector_search(query, top_k=3, tau=0.3, use_rgcn=False)
            if sbert_results['success']:
                print(f"✅ SBERT 검색 성공: {len(sbert_results['search_results'])}개 결과")
                client.print_search_results(sbert_results['search_results'], sbert_results['triples'])
            else:
                print(f"❌ SBERT 검색 실패: {sbert_results.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ SBERT 검색 예외: {e}")
    
    print(f"\n{'='*50}")
    print("🎉 테스트 완료")
    print('='*50)


def test_rgcn_model_only():
    """R-GCN 모델만 단독 테스트"""
    print("🧪 R-GCN 모델 단독 테스트 시작")
    
    try:
        from rgcn_model import RGCNEmbedder
        
        # R-GCN 임베더 초기화
        embedder = RGCNEmbedder(
            model_path="model/embed_triplet_struct_ver1+2/best_model.pt",
            edge_map_path="config/graph/edge_type_map.json"
        )
        
        print("✅ R-GCN 모델 초기화 성공")
        
        # 테스트 triple들
        test_triples = [
            ("person:man", "walk", "object:street"),
            ("person:woman", "drive", "object:car"),
            ("person:child", "eat", "object:food"),
            ("person:man", "talk", None)
        ]
        
        for i, (subject, verb, obj) in enumerate(test_triples, 1):
            print(f"\n테스트 {i}: {subject} -> {verb} -> {obj}")
            try:
                subj_emb, verb_emb, obj_emb = embedder.embed_triple_with_rgcn(subject, verb, obj)
                print(f"  Subject 임베딩: {subj_emb.shape if subj_emb is not None else 'None'}")
                print(f"  Verb 임베딩: {verb_emb.shape if verb_emb is not None else 'None'}")
                print(f"  Object 임베딩: {obj_emb.shape if obj_emb is not None else 'None'}")
            except Exception as e:
                print(f"  ❌ 임베딩 실패: {e}")
        
        print("\n✅ R-GCN 모델 단독 테스트 완료")
        
    except Exception as e:
        print(f"❌ R-GCN 모델 테스트 실패: {e}")


if __name__ == "__main__":
    print("🚀 R-GCN 그래프 임베딩 검색 테스트 시작")
    
    # 1. R-GCN 모델 단독 테스트
    test_rgcn_model_only()
    
    # 2. 전체 검색 시스템 테스트
    test_rgcn_search()
