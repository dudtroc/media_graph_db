#!/usr/bin/env python3
"""
최적화된 Triple 검색 테스트 스크립트
기존 검색과 성능 비교
"""

import os
import sys
import time
from scene_graph_client import SceneGraphDBClient
from optimized_triple_search import OptimizedTripleSearcher

def test_performance_comparison():
    """성능 비교 테스트"""
    print("🚀 Triple 검색 성능 비교 테스트")
    print("=" * 80)
    
    # 클라이언트 초기화
    try:
        client = SceneGraphDBClient()
        searcher = OptimizedTripleSearcher(client)
        print("✅ 클라이언트 초기화 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # API 서버 연결 확인
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return
    
    # 테스트 쿼리들
    test_queries = [
        "키스 하는 장면을 찾아줘",
        "사람이 걷는 장면을 찾아줘",
        "차를 운전하는 장면을 찾아줘",
        "두 사람이 대화하는 장면을 찾아줘",
        "요리하는 장면을 찾아줘"
    ]
    
    print(f"📋 테스트 쿼리: {len(test_queries)}개")
    print("-" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*20} 테스트 {i}/{len(test_queries)} {'='*20}")
        print(f"🔍 쿼리: {query}")
        
        # 1. 기존 방법 (vector_search)
        print(f"\n📊 기존 방법 (vector_search) 테스트:")
        try:
            start_time = time.time()
            result_original = client.vector_search(query, top_k=5, tau=0.30, use_rgcn=True)
            end_time = time.time()
            original_time = end_time - start_time
            
            if result_original['success']:
                print(f"  ✅ 성공: {len(result_original['search_results'])}개 결과")
                print(f"  ⏱️  소요시간: {original_time:.2f}초")
                print(f"  📝 생성된 triple: {len(result_original['triples'])}개")
            else:
                print(f"  ❌ 실패: {result_original.get('error', 'Unknown error')}")
                original_time = float('inf')
                
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            original_time = float('inf')
        
        # 2. 최적화된 방법 (OptimizedTripleSearcher)
        print(f"\n🚀 최적화된 방법 (OptimizedTripleSearcher) 테스트:")
        try:
            # 질문을 triple로 변환
            from reference_query_to_triples_converter import QueryToTriplesConverter
            
            converter = QueryToTriplesConverter(
                qa_template_path="templates/qa_to_triple_template.txt",
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini"
            )
            
            triples = converter.convert_question(query)
            if not triples:
                print(f"  ❌ 질문을 triple로 변환할 수 없습니다.")
                continue
            
            print(f"  📝 생성된 triple: {len(triples)}개")
            for j, triple in enumerate(triples, 1):
                print(f"    {j}. {' | '.join(str(t) for t in triple)}")
            
            start_time = time.time()
            result_optimized = searcher.search_triples_optimized(triples, tau=0.30, top_k=5, use_rgcn=True)
            end_time = time.time()
            optimized_time = end_time - start_time
            
            print(f"  ✅ 성공: {len(result_optimized)}개 결과")
            print(f"  ⏱️  소요시간: {optimized_time:.2f}초")
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            optimized_time = float('inf')
        
        # 3. 성능 비교
        print(f"\n📈 성능 비교:")
        if original_time != float('inf') and optimized_time != float('inf'):
            speedup = original_time / optimized_time
            print(f"  기존 방법: {original_time:.2f}초")
            print(f"  최적화 방법: {optimized_time:.2f}초")
            print(f"  성능 향상: {speedup:.2f}x {'빠름' if speedup > 1 else '느림'}")
        else:
            print(f"  비교 불가 (오류 발생)")
        
        # 4. 결과 품질 비교
        print(f"\n🎯 결과 품질 비교:")
        if result_original.get('success') and result_optimized:
            original_count = len(result_original['search_results'])
            optimized_count = len(result_optimized)
            print(f"  기존 방법 결과: {original_count}개")
            print(f"  최적화 방법 결과: {optimized_count}개")
            
            if original_count > 0 and optimized_count > 0:
                # 상위 3개 결과 비교
                print(f"  상위 결과 비교:")
                for j in range(min(3, original_count, optimized_count)):
                    orig = result_original['search_results'][j]
                    opt = result_optimized[j]
                    print(f"    {j+1}. 기존: {orig['drama_name']} {orig['episode_number']} "
                          f"(매치: {orig['match_count']}, 유사도: {orig['avg_similarity']:.3f})")
                    print(f"       최적화: {opt['drama_name']} {opt['episode_number']} "
                          f"(매치: {opt['match_count']}, 유사도: {opt['avg_similarity']:.3f})")

def test_single_query_detailed():
    """단일 쿼리 상세 테스트"""
    print("\n" + "=" * 80)
    print("🔍 단일 쿼리 상세 테스트")
    print("=" * 80)
    
    # 클라이언트 초기화
    try:
        client = SceneGraphDBClient()
        searcher = OptimizedTripleSearcher(client)
        print("✅ 클라이언트 초기화 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # API 서버 연결 확인
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return
    
    query = "키스 하는 장면을 찾아줘"
    print(f"🔍 테스트 쿼리: '{query}'")
    
    # 질문을 triple로 변환
    try:
        from reference_query_to_triples_converter import QueryToTriplesConverter
        
        converter = QueryToTriplesConverter(
            qa_template_path="templates/qa_to_triple_template.txt",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini"
        )
        
        triples = converter.convert_question(query)
        if not triples:
            print("❌ 질문을 triple로 변환할 수 없습니다.")
            return
        
        print(f"✅ {len(triples)}개 triple 생성 완료:")
        for i, triple in enumerate(triples, 1):
            print(f"  {i}. {' | '.join(str(t) for t in triple)}")
        
        # 최적화된 검색 수행
        print(f"\n🚀 최적화된 검색 수행:")
        start_time = time.time()
        results = searcher.search_triples_optimized(triples, tau=0.30, top_k=5, use_rgcn=True)
        end_time = time.time()
        search_time = end_time - start_time
        
        print(f"✅ 검색 완료: {len(results)}개 결과 (소요시간: {search_time:.2f}초)")
        
        # 상세 결과 출력
        if results:
            print(f"\n🎬 상세 검색 결과:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['drama_name']} {result['episode_number']} - 장면 {result['scene_number']}")
                print(f"     매치: {result['match_count']}/{result['total_queries']}개")
                print(f"     평균 유사도: {result['avg_similarity']:.3f}")
                print(f"     매칭된 triple: {len(result['matched_triples'])}개")
                
                # 매칭된 triple 상세 정보
                for j, match in enumerate(result['matched_triples'], 1):
                    print(f"       {j}. Triple {match[0]+1}: 유사도 {match[1]:.3f}")
        else:
            print("⚠️ 검색 결과가 없습니다.")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "performance":
            test_performance_comparison()
        elif command == "detailed":
            test_single_query_detailed()
        else:
            print("사용법:")
            print("  python test_optimized_search.py performance  # 성능 비교 테스트")
            print("  python test_optimized_search.py detailed     # 상세 테스트")
    else:
        # 기본적으로 성능 비교 테스트 실행
        test_performance_comparison()

if __name__ == "__main__":
    main()
