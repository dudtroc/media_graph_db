#!/usr/bin/env python3
"""
벡터 검색 예시 코드
"키스 하는 장면을 찾아줘" 쿼리로 DB에서 검색하는 예시
"""

import os
import sys
import time
from scene_graph_client import SceneGraphDBClient

def test_kiss_search():
    """키스하는 장면 검색 테스트"""
    print("💋 키스하는 장면 검색 테스트")
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
    
    # 검색 쿼리
    query = "키스 하는 장면을 찾아줘"
    top_k = 5
    tau = 0.30
    
    print(f"🔍 검색 쿼리: '{query}'")
    print(f"📊 검색 설정: top_k={top_k}, tau={tau}")
    print("-" * 60)
    
    try:
        # 벡터 검색 수행 (R-GCN 그래프 임베딩 사용)
        result = client.vector_search(query, top_k, tau, use_rgcn=True)
        
        if result['success']:
            print(f"✅ 검색 성공!")
            print(f"📝 생성된 triple 수: {len(result['triples'])}")
            print(f"🎯 검색 결과 수: {len(result['search_results'])}")
            
            # 생성된 triples 출력
            if result['triples']:
                print(f"\n📋 생성된 triples:")
                for i, triple in enumerate(result['triples'], 1):
                    print(f"  {i}. {' | '.join(str(t) for t in triple)}")
            
            # 검색 결과 출력
            if result['search_results']:
                print(f"\n🎬 검색 결과:")
                client.print_search_results(result['search_results'], result['triples'])
            else:
                print(f"\n⚠️ 검색 결과가 없습니다. (유사도 임계값: {tau})")
                print(f"💡 임계값을 낮춰보세요: tau=0.20")
        else:
            print(f"❌ 검색 실패: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")

def test_multiple_queries():
    """여러 쿼리로 검색 테스트"""
    print("\n" + "=" * 60)
    print("🔍 다양한 쿼리 검색 테스트")
    print("=" * 60)
    
    # 클라이언트 초기화
    try:
        client = SceneGraphDBClient()
    except Exception as e:
        print(f"❌ 클라이언트 초기화 실패: {e}")
        return
    
    # API 서버 연결 확인
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return
    
    # 테스트 쿼리 목록
    test_queries = [
        "키스 하는 장면을 찾아줘",
        "사람이 걷는 장면을 찾아줘", 
        "차를 운전하는 장면을 찾아줘",
        "두 사람이 대화하는 장면을 찾아줘",
        "요리하는 장면을 찾아줘"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*20} 테스트 {i}/{len(test_queries)} {'='*20}")
        print(f"🔍 쿼리: {query}")
        
        try:
            # 벡터 검색 수행 (R-GCN 그래프 임베딩 사용)
            result = client.vector_search(query, top_k=3, tau=0.25, use_rgcn=True)
            
            if result['success']:
                print(f"✅ 검색 성공! 결과 {len(result['search_results'])}개")
                
                # 간단한 결과 요약
                if result['search_results']:
                    for j, scene_result in enumerate(result['search_results'][:2], 1):  # 상위 2개만
                        print(f"  {j}. 장면 ID {scene_result['scene_id']}: "
                              f"매치 {scene_result['match_count']}개, "
                              f"유사도 {scene_result['avg_similarity']:.3f}")
                else:
                    print("  ⚠️ 검색 결과 없음")
            else:
                print(f"❌ 검색 실패: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 검색 중 오류: {e}")

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "kiss":
            test_kiss_search()
        elif command == "multiple":
            test_multiple_queries()
        else:
            print("사용법:")
            print("  python test_vector_search_example.py kiss        # 키스 검색")
            print("  python test_vector_search_example.py multiple    # 여러 쿼리 테스트")
    else:
        # 기본적으로 키스 검색 실행
        test_kiss_search()

if __name__ == "__main__":
    main()
