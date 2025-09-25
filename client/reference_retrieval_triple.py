#!/usr/bin/env python3
# test_step4_retrieval_triple.py  –  multi-triple retrieval + partial match
# ------------------------------------------------------------------------
from __future__ import annotations

import os, json, ast, yaml, heapq, argparse, torch
import torch.nn.functional as F
from pathlib import Path
from typing import List, Tuple, Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from openai import OpenAI                        # openai-python ≥1.x
from dotenv import load_dotenv

load_dotenv()

# ───────── 경로 & 상수 ──────────────────────────────────────────
DATASET   = "drama_media_data"  # "dummy" or "media_data" or "drama_media_data"
JSON_ROOT = Path(f"output/{DATASET}/scene_graph_class/gpt-4o")
Z_CACHE   = Path(f"cache/cached_graphs_{DATASET}_embed_fixed_z_ver1+2")
BERT_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEVICE    = "cuda" if torch.cuda.is_available() else "cpu"
TOP_K     = 5

# ───────── SBERT ───────────────────────────────────────────────
sbert = SentenceTransformer(BERT_NAME, device=DEVICE).eval()

@torch.no_grad()
def vec(txt: str) -> torch.Tensor:
    return torch.tensor(
        sbert.encode(txt, max_length=32, normalize_embeddings=True),
        dtype=torch.float32
    )

# ───────── LLM util ────────────────────────────────────────────
def extract_list(txt: str) -> List:
    start, end = txt.find("["), txt.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        return ast.literal_eval(txt[start : end + 1])
    except Exception:
        return []

# QueryToTriplesConverter 클래스 import 추가
from reference_query_to_triples_converter import QueryToTriplesConverter

# query_to_triples 함수를 클래스로 대체
def query_to_triples(client: OpenAI, tmpl: str, q: str,
                     model="gpt-4o-mini") -> List[List[str]]:
    # 기존 함수는 호환성을 위해 유지하되, 내부적으로 클래스 사용
    converter = QueryToTriplesConverter(
        base_config_path="config/base_params.yaml",
        model=model
    )
    return converter(q)

# ───────── Scene-Graph helpers ─────────────────────────────────
def triples_in_scene(js) -> List[Tuple[int,int,Optional[int],str]]:
    out, g = [], js["scene_graph"]
    for ev in g.get("events", []):
        s, o = ev.get("subject"), ev.get("object")
        if s is None:
            continue
        # object가 정수 ID가 아닐 경우 None 처리
        o = o if isinstance(o, int) else None
        out.append((s, ev["event_id"], o, ev.get("verb", "")))
    return out

def token_to_sentence(tok: str | None) -> str:
    if not tok:
        return ""
    sup, typ = tok.split(":", 1) if ":" in tok else (tok, tok)
    return f"A {typ} which is a kind of {sup}."

def embed_query(tokens: List[str]) -> Tuple[torch.Tensor|None, ...]:
    s_tok, v_tok, o_tok = (tokens + [None, None])[:3]
    q_s = vec(token_to_sentence(s_tok)) if s_tok else None
    q_v = vec(v_tok)                     if v_tok else None
    q_o = (
        vec(token_to_sentence(o_tok))
        if o_tok not in (None, "", "none", "None") else None
    )
    return q_s, q_v, q_o

def describe_nodes(js_path: Path, sid:int,eid:int,oid:Optional[int]):
    js = json.load(js_path.open()); g = js["scene_graph"]
    om = {o["object_id"]:o for o in g.get("objects", [])}
    em = {e["event_id"]:e for e in g.get("events",  [])}
    s_txt = f"{om[sid]['type of']}({om[sid]['super_type']})" if sid in om else "?"
    v_txt = em.get(eid, {}).get("verb", "?")
    o_txt = "-" if oid is None else (
        f"{om[oid]['type of']}({om[oid]['super_type']})" if oid in om else "?"
    )
    return s_txt, v_txt, o_txt

# ───────── 검색 (multi-triple, partial match) ─────────────────
def search_topk_multi(queries_emb: List[Tuple], tau: float, k=TOP_K):
    heap=[]
    total_q=len(queries_emb)

    for pt_fp in tqdm(list(Z_CACHE.rglob("*.pt")), desc="search"):
        blob=torch.load(pt_fp, map_location="cpu")
        z=F.normalize(blob["z"], dim=1)
        id2idx={nid:i for i,nid in enumerate(blob["orig_id"])}

        rel_path = Path(blob["path"])
        js_fp    = JSON_ROOT / rel_path
        if not js_fp.exists(): continue
        scene_triples = triples_in_scene(json.load(js_fp.open()))
        if not scene_triples: continue

        matched=[]; used=set()

        for q_idx,(q_s,q_v,q_o) in enumerate(queries_emb):
            best=None
            for sid,eid,oid,_ in scene_triples:
                # triple의 각 요소가 list인 경우 스킵
                if any(isinstance(x, list) for x in (sid, eid, oid)):
                    continue
                if sid not in id2idx or eid not in id2idx: continue
                # 객체 필수 여부 판단
                need_obj = q_o is not None
                if need_obj and oid is None:              continue

                v_s = z[id2idx[sid]]
                v_v = z[id2idx[eid]]
                v_o = z[id2idx[oid]] if (oid is not None and oid in id2idx) else None

                # 객체 유효성 점검
                if need_obj and v_o is None: continue

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

                sims=[x for x in (s_sim,v_sim,o_sim) if x is not None]
                sim=sum(sims)/len(sims)

                if best is None or sim > best[0]:
                    best=(sim,s_sim,v_sim,o_sim,(sid,eid,oid))
            if best:
                matched.append((q_idx,)+best)
                used.add(best[-1])

        if not matched: continue
        match_cnt=len(matched); avg_sim=sum(m[1] for m in matched)/match_cnt
        heapq.heappush(heap,(match_cnt,avg_sim,matched,rel_path.parts[0],rel_path,total_q))
        if len(heap)>k: heapq.heappop(heap)

    return sorted(heap,key=lambda x:(-x[0],-x[1]))

# ───────── 출력 ───────────────────────────────────────────────
def print_results_multi(res, query_tokens: List[List[str]]):
    if not res:
        print("No scene matched."); return
    print("\n=== Top-k Scene Graphs ===")
    for rk,(cnt,avg_sim,matched,drama,rel,total_q) in enumerate(res,1):
        print(f"\n{rk}. Scene = {drama}/{rel.name}")
        print(f"    ✔ matched {cnt}/{total_q} triples | avg_sim = {avg_sim:.3f}")

        m_dict={q:(sim,s_sim,v_sim,o_sim,ids) for q,sim,s_sim,v_sim,o_sim,ids in matched}
        for q_idx,toks in enumerate(query_tokens):
            q_txt=" | ".join(str(t) for t in toks)
            if q_idx in m_dict:
                sim,s_sim,v_sim,o_sim,ids=m_dict[q_idx]
                s_desc,v_desc,o_desc=describe_nodes(JSON_ROOT/rel,*ids)
                f=lambda x:f"{x: .3f}" if x is not None else "--"
                print(f"    • Q{q_idx}: sim={sim:.3f} (S={f(s_sim)}, V={f(v_sim)}, O={f(o_sim)})")
                print(f"        ↳ matched: {s_desc} / {v_desc} / {o_desc}")
            else:
                print(f"    • Q{q_idx}: (미탐) {q_txt}")
 
# ───────── 메인 ───────────────────────────────────────────────
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--question",
        default="남녀가 키스하는 장면을 찾아줘.")
    ap.add_argument("--tau_comp",type=float,default=0.30)
    ap.add_argument("--topk",type=int,default=TOP_K)
    args=ap.parse_args()

    # 0. OpenAI
    api_key=os.getenv("OPEN_AI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPEN_AI_API_KEY not set")
    client=OpenAI(api_key=api_key)

    # 1. LLM → triples (클래스 사용)
    print(f"질의: {args.question}")
    
    # QueryToTriplesConverter 클래스 사용
    converter = QueryToTriplesConverter(
        base_config_path="config/base_params.yaml",
        model="gpt-4o-mini"
    )
    
    tokens = converter(args.question)
    print("LLM triple tokens:", tokens)
    if not tokens: quit("❌ LLM parsing failed.")

    # 2. 질의 임베딩
    queries_emb=[embed_query(t) for t in tokens]

    # 3. 검색
    results=search_topk_multi(queries_emb,args.tau_comp,args.topk)

    # 4. 출력
    print_results_multi(results,tokens)
