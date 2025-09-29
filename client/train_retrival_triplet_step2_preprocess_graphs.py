#!/usr/bin/env python
# preprocess_scene_graph_with_edge_map.py (fixed: object_of_event 오류 및 debug 로그 추가)

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict

import torch
from torch_geometric.data import HeteroData
from sentence_transformers import SentenceTransformer

# ▪ CONFIG
MEDIA_SET = "drama_media_data" # "dummy" or "media_data" or "drama_media_data"
DATA_DIR = Path(f"output/{MEDIA_SET}/scene_graph_class_ver2/gpt-4o")
CACHE_DIR = Path(f"cache/cached_graphs_{MEDIA_SET}_embed_fixed_from_string_ver2")
EDGE_MAP_PATH = Path("config/graph/edge_type_map.json")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ▪ Load edge_type map
if not EDGE_MAP_PATH.exists():
    sys.exit(f"❌ edge_type_map.json not found: {EDGE_MAP_PATH}")
with EDGE_MAP_PATH.open() as f:
    EDGE2ID: Dict[str,int] = json.load(f)

# ▪ Sentence-BERT
model = SentenceTransformer(MODEL_NAME, device=DEVICE).eval()
@torch.no_grad()
def embed(txt: str) -> torch.Tensor:
    return torch.tensor(model.encode(txt, max_length=32, normalize_embeddings=True), dtype=torch.float32)

_txt_cache: Dict[str, torch.Tensor] = {}
def vec(t: str) -> torch.Tensor:
    if t not in _txt_cache:
        _txt_cache[t] = embed(t).cpu()
    return _txt_cache[t]

def extract_id(x):
    if isinstance(x, dict):
        for k in ("object_id", "event_id", "spatial_id", "temporal_id"):
            if k in x: return x[k]
    if isinstance(x, int): return x
    return None

def decode_edge_key(et_name: str):
    parts = et_name.split("_")
    if len(parts) < 3: return None, None, None
    st = parts[0]; dt = parts[-1]; rel = "_".join(parts[1:-1])
    return st, rel, dt

def json_to_data(js: dict, file_name="(unknown)") -> HeteroData | None:
    if not isinstance(js, dict) or "scene_graph" not in js:
        return None

    g = js["scene_graph"]
    data, nid_map = HeteroData(), {}

    meta = g.get("meta", {})
    scene_txt = f"place {meta.get('scene_place','')} time {meta.get('scene_time','')} atmosphere {meta.get('scene_atmosphere','')}".strip()
    data["scene"].x = vec(scene_txt or "scene").unsqueeze(0)
    data["scene"].node_type = torch.full((1,), 0)
    scene_idx = 0

    obj_feats = []; obj_types = []
    for o in g.get("objects", []):
        # text = f"[SUPER TYPE] {o.get('super_type', '')}, [TYPE] {o.get('type of', '')}"
        text = f"A {o.get('type of', '')} which is a kind of {o.get('super_type', '')}."
        obj_feats.append(vec(text))
        obj_types.append(o.get("type of", "unknown"))
        nid_map[o["object_id"]] = ("object", len(obj_feats) - 1)
    data["object"].x = torch.stack(obj_feats) if obj_feats else torch.empty((0,384))
    data["object"].node_type = torch.full((len(obj_feats),), 1)
    data["object"].label_text = obj_types

    evt_feats, evt_verbs = [], []
    for ev in g.get("events", []):
        # text = f"[VERB] {ev.get('verb','')}"
        text = f"{ev.get('verb','')}"
        evt_feats.append(vec(text))
        evt_verbs.append(ev.get("verb", "unknown"))
        nid_map[ev["event_id"]] = ("event", len(evt_feats) - 1)
    data["event"].x = torch.stack(evt_feats) if evt_feats else torch.empty((0,384))
    data["event"].node_type = torch.full((len(evt_feats),), 2)
    data["event"].label_text = evt_verbs

    spat_feats, spat_preds = [], []
    for sp in g.get("spatial", []):
        # text = f"[PREDICATE] {sp.get('predicate', '')}"
        text = f"{sp.get('predicate', '')}"
        spat_feats.append(vec(text))
        spat_preds.append(sp.get("predicate", "unknown"))
        nid_map[sp["spatial_id"]] = ("spatial", len(spat_feats) - 1)
    data["spatial"].x = torch.stack(spat_feats) if spat_feats else torch.empty((0,384))
    data["spatial"].node_type = torch.full((len(spat_feats),), 3)
    data["spatial"].label_text = spat_preds

    edge_idx_dict, edge_typ_dict = defaultdict(list), defaultdict(list)

    def safe_add_edge(src_id, dst_id, rel, file=None, event_id=None):
        if src_id not in nid_map or dst_id not in nid_map:
            return
        st, si = nid_map[src_id]; dt, di = nid_map[dst_id]
        rel_name = f"{st}_{rel}_{dt}"
        if rel_name not in EDGE2ID:
            print(f"[skip] unknown rel_name: {rel_name} | file={file} | ev_id={event_id}")
            return
        eid = EDGE2ID[rel_name]
        edge_idx_dict[(st, rel, dt)].append([si, di])
        edge_typ_dict[(st, rel, dt)].append(eid)

    for o in g.get("objects", []):
        safe_add_edge(scene_idx, o["object_id"], "in_scene", file=file_name)
        safe_add_edge(o["object_id"], scene_idx, "to_scene", file=file_name)
    for ev in g.get("events", []):
        safe_add_edge(scene_idx, ev["event_id"], "in_scene", file=file_name)
        safe_add_edge(ev["event_id"], scene_idx, "to_scene", file=file_name)
        subj = extract_id(ev.get("subject")); obj = extract_id(ev.get("object"))
        if subj is not None:
            safe_add_edge(subj, ev["event_id"], "subject_of_event", file=file_name, event_id=ev.get("event_id"))
        if obj is not None:
            # ✅ object 노드만 연결하도록 필터링
            if nid_map.get(obj, (None,))[0] == "object":
                safe_add_edge(ev["event_id"], obj, "object_of_event", file=file_name, event_id=ev.get("event_id"))
    for sp in g.get("spatial", []):
        safe_add_edge(sp["subject"], sp["spatial_id"], "subject_of_spatial", file=file_name)
        obj_id = sp.get("object", None)
        # obj_id가 int가 아니면 스킵
        if isinstance(obj_id, int) and nid_map.get(obj_id, (None,))[0] == "object":
            safe_add_edge(sp["spatial_id"], obj_id, "object_of_spatial", file=file_name)
    for tm in g.get("temporal", []):
        safe_add_edge(tm["subject"], tm["object"], "before", file=file_name)

    for key, pairs in edge_idx_dict.items():
        et_name = f"{key[0]}_{key[1]}_{key[2]}"
        eid = EDGE2ID[et_name]
        data[key].edge_index = torch.tensor(pairs, dtype=torch.long).t()
        data[key].edge_type = torch.full((len(pairs),), eid, dtype=torch.long)

    for et_name, eid in EDGE2ID.items():
        st, rel, dt = decode_edge_key(et_name)
        if None in (st, rel, dt): continue
        key = (st, rel, dt)
        if key not in data.edge_types:
            data[key].edge_index = torch.empty((2, 0), dtype=torch.long)
            data[key].edge_type = torch.full((0,), eid, dtype=torch.long)

    return data

def main():
    json_files = list(DATA_DIR.rglob("*.json"))
    print(f"✓ Found {len(json_files)} JSON files")

    for jp in json_files:
        out_pt = CACHE_DIR / jp.relative_to(DATA_DIR).with_suffix(".pt")
        if out_pt.exists(): continue

        with jp.open(encoding="utf-8") as f:
            js = json.load(f)
        data = json_to_data(js, file_name=str(jp))
        if data is None: continue

        homo = data.to_homogeneous(
            node_attrs=["x", "node_type"],
            add_node_type=True,
            add_edge_type=False
        )
        out_pt.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"data": homo, "path": str(jp.relative_to(DATA_DIR))}, out_pt)

    if _txt_cache:
        torch.save(torch.stack(list(_txt_cache.values())), CACHE_DIR / "unique_texts.pt")

if __name__ == "__main__":
    main()
