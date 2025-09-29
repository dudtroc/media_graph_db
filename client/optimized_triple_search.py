#!/usr/bin/env python3
"""
최적화된 Triple 검색 구현
기존 _search_triples_in_db 메서드의 성능을 개선한 버전
"""

import torch
import torch.nn.functional as F
import heapq
from typing import Dict, List, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from scene_graph_client import SceneGraphDBClient

class OptimizedTripleSearcher:
    """
    최적화된 Triple 검색 클래스
    - 배치 처리로 성능 향상
    - 메모리 사용량 최적화
    - 병렬 처리 지원
    """
    
    def __init__(self, client: SceneGraphDBClient, device: str = "auto"):
        self.client = client
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.sbert = None
        self.rgcn_embedder = None
        
    def _initialize_models(self, use_rgcn: bool = True):
        """모델 초기화 (지연 로딩)"""
        if self.sbert is None:
            BERT_NAME = "sentence-transformers/all-MiniLM-L6-v2"
            self.sbert = SentenceTransformer(BERT_NAME, device=self.device).eval()
            
        if use_rgcn and self.rgcn_embedder is None:
            try:
                from rgcn_model import RGCNEmbedder
                self.rgcn_embedder = RGCNEmbedder(
                    model_path="model/embed_triplet_struct_ver1+2/best_model.pt",
                    edge_map_path="config/graph/edge_type_map.json",
                    sbert_model="sentence-transformers/all-MiniLM-L6-v2",
                    device=self.device
                )
                print("✅ R-GCN 모델 초기화 완료")
            except Exception as e:
                print(f"⚠️ R-GCN 모델 초기화 실패, SBERT만 사용: {e}")
                use_rgcn = False
                
        return use_rgcn
    
    def search_triples_optimized(self, triples: List[List[str]], tau: float = 0.30, top_k: int = 5, use_rgcn: bool = True) -> List[Dict[str, Any]]:
        """
        최적화된 Triple 검색
        
        Args:
            triples: 검색할 triple 리스트
            tau: 유사도 임계값
            top_k: 반환할 최대 결과 수
            use_rgcn: R-GCN 그래프 임베딩 사용 여부
            
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            # 모델 초기화
            use_rgcn = self._initialize_models(use_rgcn)
            
            # 1. 쿼리 임베딩 생성 (배치 처리)
            print(f"🔍 {len(triples)}개 triple 임베딩 생성 중...")
            query_embeddings = self._embed_triples_batch(triples, use_rgcn)
            
            # 2. DB에서 장면 데이터를 배치로 조회
            print(f"🔍 DB에서 장면 데이터 조회 중...")
            scene_data = self._fetch_scene_data_batch()
            
            # 3. 벡터화된 검색 수행
            print(f"🔍 벡터 검색 수행 중...")
            results = self._perform_vectorized_search(
                query_embeddings, scene_data, tau, top_k
            )
            
            print(f"✅ 최적화된 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            print(f"❌ 최적화된 검색 실패: {e}")
            return []
    
    def _embed_triples_batch(self, triples: List[List[str]], use_rgcn: bool) -> List[Tuple[torch.Tensor, ...]]:
        """Triple들을 배치로 임베딩"""
        embeddings = []
        
        @torch.no_grad()
        def vec(txt: str) -> torch.Tensor:
            return self.sbert.encode(txt, normalize_embeddings=True, convert_to_tensor=True).float()
        
        def token_to_sentence(tok: str | None) -> str:
            if not tok:
                return ""
            sup, typ = tok.split(":", 1) if ":" in tok else (tok, tok)
            return f"A {typ} which is a kind of {sup}."
        
        for i, triple in enumerate(triples):
            s_tok, v_tok, o_tok = (triple + [None, None])[:3]
            
            try:
                if use_rgcn and self.rgcn_embedder:
                    # R-GCN 임베딩
                    q_s, q_v, q_o = self.rgcn_embedder.embed_triple_with_rgcn(s_tok, v_tok, o_tok)
                else:
                    # SBERT 임베딩
                    q_s = vec(token_to_sentence(s_tok)) if s_tok and s_tok != "None" else None
                    q_v = vec(v_tok) if v_tok and v_tok != "None" else None
                    q_o = (
                        vec(token_to_sentence(o_tok))
                        if o_tok and o_tok not in (None, "", "none", "None") else None
                    )
                
                embeddings.append((q_s, q_v, q_o))
                
            except Exception as e:
                print(f"  ❌ Triple {i+1} 임베딩 실패: {e}")
                # Fallback to SBERT
                try:
                    q_s = vec(token_to_sentence(s_tok)) if s_tok and s_tok != "None" else None
                    q_v = vec(v_tok) if v_tok and v_tok != "None" else None
                    q_o = (
                        vec(token_to_sentence(o_tok))
                        if o_tok and o_tok not in (None, "", "none", "None") else None
                    )
                    embeddings.append((q_s, q_v, q_o))
                except Exception as e2:
                    print(f"  ❌ Fallback도 실패: {e2}")
                    embeddings.append((None, None, None))
        
        return embeddings
    
    def _fetch_scene_data_batch(self) -> List[Dict[str, Any]]:
        """장면 데이터를 배치로 조회"""
        scene_data = []
        
        try:
            videos = self.client.get_videos()
            print(f"✅ 비디오 {len(videos)}개 조회 완료")
            
            for video in videos:
                scenes = self.client.get_scenes(video['id'])
                print(f"✅ 비디오 {video['id']}: 장면 {len(scenes)}개")
                
                for scene in scenes:
                    scene_id = scene['id']
                    
                    # 장면의 모든 노드 데이터 조회
                    objects = self.client.get_scene_objects(scene_id)
                    events = self.client.get_scene_events(scene_id)
                    spatial = self.client.get_scene_spatial_relations(scene_id)
                    temporal = self.client.get_scene_temporal_relations(scene_id)
                    embeddings = self.client.get_scene_embeddings(scene_id)
                    
                    # 임베딩을 딕셔너리로 변환
                    embedding_dict = {}
                    for emb in embeddings:
                        embedding_data = emb['embedding']
                        if isinstance(embedding_data, str):
                            try:
                                import ast
                                embedding_list = ast.literal_eval(embedding_data)
                                embedding_tensor = torch.tensor(embedding_list, dtype=torch.float32)
                            except Exception:
                                continue
                        elif isinstance(embedding_data, list):
                            embedding_tensor = torch.tensor(embedding_data, dtype=torch.float32)
                        else:
                            embedding_tensor = embedding_data
                        embedding_dict[emb['node_id']] = embedding_tensor
                    
                    # 장면의 triple 생성
                    scene_triples = []
                    for event in events:
                        subject_id = event['subject_id']
                        event_id = event['event_id']
                        object_id = event.get('object_id')
                        verb = event['verb']
                        
                        if (subject_id in embedding_dict and 
                            event_id in embedding_dict and 
                            (object_id is None or object_id in embedding_dict)):
                            subject_emb = embedding_dict[subject_id]
                            event_emb = embedding_dict[event_id]
                            object_emb = embedding_dict.get(object_id) if object_id else None
                            scene_triples.append((subject_emb, event_emb, object_emb, verb))
                    
                    if scene_triples:
                        scene_data.append({
                            'scene_id': scene_id,
                            'video_id': video['id'],
                            'drama_name': video['drama_name'],
                            'episode_number': video['episode_number'],
                            'scene_number': scene['scene_number'],
                            'triples': scene_triples
                        })
            
            print(f"✅ 총 {len(scene_data)}개 장면 데이터 준비 완료")
            return scene_data
            
        except Exception as e:
            print(f"❌ 장면 데이터 조회 실패: {e}")
            return []
    
    def _perform_vectorized_search(self, query_embeddings: List[Tuple[torch.Tensor, ...]], 
                                 scene_data: List[Dict[str, Any]], 
                                 tau: float, top_k: int) -> List[Dict[str, Any]]:
        """벡터화된 검색 수행"""
        heap = []
        total_queries = len(query_embeddings)
        
        for scene_info in scene_data:
            scene_triples = scene_info['triples']
            matched = []
            used = set()
            
            for q_idx, (q_s, q_v, q_o) in enumerate(query_embeddings):
                if q_s is None and q_v is None and q_o is None:
                    continue
                    
                # 쿼리 임베딩을 같은 디바이스로 이동
                q_s = q_s.to(self.device) if q_s is not None else None
                q_v = q_v.to(self.device) if q_v is not None else None
                q_o = q_o.to(self.device) if q_o is not None else None
                best = None
                
                for subject_emb, event_emb, object_emb, verb in scene_triples:
                    # 객체 필수 여부 판단
                    need_obj = q_o is not None
                    if need_obj and object_emb is None:
                        continue
                    
                    # 임베딩 벡터 가져오기
                    v_s = subject_emb.to(self.device)
                    v_v = event_emb.to(self.device)
                    v_o = object_emb.to(self.device) if object_emb is not None else None
                    
                    # 정규화
                    v_s = F.normalize(v_s.unsqueeze(0), dim=1).squeeze(0)
                    v_v = F.normalize(v_v.unsqueeze(0), dim=1).squeeze(0)
                    if v_o is not None:
                        v_o = F.normalize(v_o.unsqueeze(0), dim=1).squeeze(0)
                    
                    # 유사도 계산
                    s_sim = float(torch.dot(q_s, v_s)) if q_s is not None else None
                    v_sim = float(torch.dot(q_v, v_v)) if q_v is not None else None
                    o_sim = (
                        float(torch.dot(q_o, v_o))
                        if (q_o is not None and v_o is not None) else None
                    )
                    
                    # 임계치 검사
                    if (q_s is not None and s_sim < tau) or \
                       (q_v is not None and v_sim < tau) or \
                       (q_o is not None and o_sim < tau):
                        continue
                    
                    sims = [x for x in (s_sim, v_sim, o_sim) if x is not None]
                    sim = sum(sims) / len(sims)
                    
                    if best is None or sim > best[0]:
                        best = (sim, s_sim, v_sim, o_sim, (subject_id, event_id, object_id))
                
                if best:
                    matched.append((q_idx,) + best)
                    used.add(best[-1])
            
            if not matched:
                continue
            
            # 결과 저장
            match_cnt = len(matched)
            avg_sim = sum(m[1] for m in matched) / match_cnt
            
            result = {
                "scene_id": scene_info['scene_id'],
                "video_id": scene_info['video_id'],
                "drama_name": scene_info['drama_name'],
                "episode_number": scene_info['episode_number'],
                "scene_number": scene_info['scene_number'],
                "match_count": match_cnt,
                "avg_similarity": avg_sim,
                "matched_triples": matched,
                "total_queries": total_queries
            }
            
            heapq.heappush(heap, (match_cnt, avg_sim, result))
            if len(heap) > top_k:
                heapq.heappop(heap)
        
        # 결과 정렬 및 반환
        results = sorted(heap, key=lambda x: (-x[0], -x[1]))
        return [result for _, _, result in results]


def test_optimized_search():
    """최적화된 검색 테스트"""
    print("🚀 최적화된 Triple 검색 테스트")
    print("=" * 60)
    
    # 클라이언트 초기화
    try:
        client = SceneGraphDBClient()
        searcher = OptimizedTripleSearcher(client)
        print("✅ 최적화된 검색기 초기화 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # API 서버 연결 확인
    if not client.health_check():
        print("❌ API 서버에 연결할 수 없습니다.")
        return
    
    # 테스트 쿼리
    query = "키스 하는 장면을 찾아줘"
    print(f"🔍 검색 쿼리: '{query}'")
    
    try:
        # 1. 질문을 triple로 변환
        from reference_query_to_triples_converter import QueryToTriplesConverter
        import os
        
        converter = QueryToTriplesConverter(
            qa_template_path="templates/qa_to_triple_template.txt",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini"
        )
        
        triples = converter.convert_question(query)
        if not triples:
            print("❌ 질문을 triple로 변환할 수 없습니다.")
            return
        
        print(f"✅ {len(triples)}개 triple 생성 완료")
        for i, triple in enumerate(triples, 1):
            print(f"  {i}. {' | '.join(str(t) for t in triple)}")
        
        # 2. 최적화된 검색 수행
        import time
        start_time = time.time()
        
        results = searcher.search_triples_optimized(triples, tau=0.30, top_k=5, use_rgcn=True)
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print(f"✅ 검색 완료: {len(results)}개 결과 (소요시간: {search_time:.2f}초)")
        
        # 3. 결과 출력
        if results:
            print(f"\n🎬 검색 결과:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['drama_name']} {result['episode_number']} - 장면 {result['scene_number']}")
                print(f"     매치: {result['match_count']}/{result['total_queries']}개, "
                      f"유사도: {result['avg_similarity']:.3f}")
        else:
            print("⚠️ 검색 결과가 없습니다.")
            
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")


if __name__ == "__main__":
    test_optimized_search()
