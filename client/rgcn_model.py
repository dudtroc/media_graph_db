#!/usr/bin/env python3
"""
R-GCN 모델을 활용한 그래프 임베딩 처리
학습된 R-GCN 모델을 로드하고 추론을 수행하는 클래스
"""

import json
import torch
import torch.nn.functional as F
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from torch_geometric.data import HeteroData, Data
from torch_geometric.nn import RGCNConv
from sentence_transformers import SentenceTransformer


class RGCNEmbedder:
    """
    R-GCN 모델을 활용한 그래프 임베딩 처리 클래스
    """
    
    def __init__(self, 
                 model_path: str = "model/embed_triplet_struct_ver1+2/best_model.pt",
                 edge_map_path: str = "config/graph/edge_type_map.json",
                 sbert_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 device: str = None):
        """
        RGCNEmbedder 초기화
        
        Args:
            model_path: 학습된 R-GCN 모델 경로
            edge_map_path: 엣지 타입 맵 파일 경로
            sbert_model: Sentence-BERT 모델명
            device: 사용할 디바이스
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = Path(model_path)
        self.edge_map_path = Path(edge_map_path)
        
        # 모델 하이퍼파라미터 (학습 시 사용된 값들)
        self.IN_DIM = 384
        self.HIDDEN = 512
        self.OUT_DIM = 384
        self.NUM_BASES = 30
        self.HOP = 1
        self.SELF_WEIGHT = 0.8
        
        # 엣지 타입 맵 로드
        self.edge2id = self._load_edge_map()
        self.num_relations = len(self.edge2id)
        
        # Sentence-BERT 모델 초기화
        self.sbert = SentenceTransformer(sbert_model, device=self.device).eval()
        
        # R-GCN 모델 초기화 및 로드
        self.model = self._load_model()
        
        print(f"✅ RGCNEmbedder 초기화 완료 - Device: {self.device}")
    
    def _load_edge_map(self) -> Dict[str, int]:
        """엣지 타입 맵 로드"""
        if not self.edge_map_path.exists():
            raise FileNotFoundError(f"Edge map file not found: {self.edge_map_path}")
        
        with self.edge_map_path.open() as f:
            edge_map = json.load(f)
        
        print(f"✅ 엣지 타입 맵 로드 완료: {len(edge_map)}개 타입")
        return edge_map
    
    def _load_model(self) -> torch.nn.Module:
        """학습된 R-GCN 모델 로드"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        # R-GCN 모델 정의
        model = RGCNModel(self.num_relations, self.IN_DIM, self.HIDDEN, self.OUT_DIM, 
                         self.NUM_BASES, self.HOP, self.SELF_WEIGHT)
        
        # 학습된 가중치 로드
        state_dict = torch.load(self.model_path, map_location=self.device, weights_only=False)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        
        print(f"✅ R-GCN 모델 로드 완료: {self.model_path}")
        return model
    
    @torch.no_grad()
    def embed_text(self, text: str) -> torch.Tensor:
        """텍스트를 Sentence-BERT로 임베딩"""
        return self.sbert.encode(text, normalize_embeddings=True, convert_to_tensor=True).float()
    
    def create_triple_subgraph(self, subject: str, verb: str, object_text: str = None) -> HeteroData:
        """
        Triple을 서브그래프로 변환
        
        Args:
            subject: 주어 (예: "person:man")
            verb: 동사 (예: "walk")
            object_text: 목적어 (예: "object:car" 또는 None)
        
        Returns:
            HeteroData: 서브그래프 데이터
        """
        data = HeteroData()
        
        # 노드 생성
        nodes = []
        node_types = []
        node_id_map = {}
        
        # Subject 노드 (object 타입)
        if subject and subject != "None":
            subj_text = self._token_to_sentence(subject)
            subj_emb = self.embed_text(subj_text)
            nodes.append(subj_emb)
            node_types.append(1)  # object type
            node_id_map[subject] = len(nodes) - 1
        
        # Verb 노드 (event 타입)
        if verb and verb != "None":
            verb_emb = self.embed_text(verb)
            nodes.append(verb_emb)
            node_types.append(2)  # event type
            node_id_map[verb] = len(nodes) - 1
        
        # Object 노드 (object 타입)
        if object_text and object_text not in ("None", "none", ""):
            obj_text = self._token_to_sentence(object_text)
            obj_emb = self.embed_text(obj_text)
            nodes.append(obj_emb)
            node_types.append(1)  # object type
            node_id_map[object_text] = len(nodes) - 1
        
        if not nodes:
            raise ValueError("유효한 노드가 없습니다.")
        
        # 노드 특성 및 타입 설정
        data["object"].x = torch.stack([nodes[i] for i, t in enumerate(node_types) if t == 1])
        data["event"].x = torch.stack([nodes[i] for i, t in enumerate(node_types) if t == 2])
        
        # 노드 타입 설정
        data["object"].node_type = torch.full((data["object"].x.size(0),), 1)
        data["event"].node_type = torch.full((data["event"].x.size(0),), 2)
        
        # 엣지 생성
        edge_indices = []
        edge_types = []
        
        # Subject -> Event 관계
        if subject in node_id_map and verb in node_id_map:
            subj_idx = node_id_map[subject]
            verb_idx = node_id_map[verb]
            edge_indices.append([subj_idx, verb_idx])
            edge_types.append(self.edge2id.get("object_subject_of_event_event", 0))
        
        # Event -> Object 관계
        if verb in node_id_map and object_text in node_id_map:
            verb_idx = node_id_map[verb]
            obj_idx = node_id_map[object_text]
            edge_indices.append([verb_idx, obj_idx])
            edge_types.append(self.edge2id.get("event_object_of_event_object", 1))
        
        # 엣지 설정
        if edge_indices:
            edge_index = torch.tensor(edge_indices, dtype=torch.long).t()
            edge_type = torch.tensor(edge_types, dtype=torch.long)
            
            # HeteroData에 엣지 추가
            if subject in node_id_map and verb in node_id_map:
                data[("object", "subject_of_event", "event")].edge_index = edge_index
                data[("object", "subject_of_event", "event")].edge_type = edge_type
            elif verb in node_id_map and object_text in node_id_map:
                data[("event", "object_of_event", "object")].edge_index = edge_index
                data[("event", "object_of_event", "object")].edge_type = edge_type
        
        return data
    
    def _token_to_sentence(self, token: str) -> str:
        """토큰을 문장으로 변환"""
        if not token:
            return ""
        if ":" in token:
            super_type, type_of = token.split(":", 1)
            return f"A {type_of} which is a kind of {super_type}."
        return token
    
    def embed_triple_with_rgcn(self, subject: str, verb: str, object_text: str = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Triple을 R-GCN으로 임베딩
        
        Args:
            subject: 주어
            verb: 동사
            object_text: 목적어
        
        Returns:
            Tuple[torch.Tensor, torch.Tensor, torch.Tensor]: (subject_emb, verb_emb, object_emb)
        """
        try:
            # 서브그래프 생성
            subgraph = self.create_triple_subgraph(subject, verb, object_text)
            
            # Homogeneous 그래프로 변환
            homo_data = subgraph.to_homogeneous(
                node_attrs=["x", "node_type"],
                add_node_type=True,
                add_edge_type=False
            )
            
            # R-GCN으로 임베딩
            with torch.no_grad():
                embeddings = self.model(
                    homo_data.x.to(self.device),
                    homo_data.edge_index.to(self.device),
                    homo_data.edge_type.to(self.device)
                )
            
            # 원래 노드 타입에 따라 임베딩 분리
            subject_emb = None
            verb_emb = None
            object_emb = None
            
            node_idx = 0
            if subject and subject != "None":
                subject_emb = embeddings[node_idx]
                node_idx += 1
            
            if verb and verb != "None":
                verb_emb = embeddings[node_idx]
                node_idx += 1
            
            if object_text and object_text not in ("None", "none", ""):
                object_emb = embeddings[node_idx]
            
            return subject_emb, verb_emb, object_emb
            
        except Exception as e:
            print(f"❌ R-GCN 임베딩 실패: {e}")
            # 실패 시 원본 SBERT 임베딩 반환
            subject_emb = self.embed_text(self._token_to_sentence(subject)) if subject and subject != "None" else None
            verb_emb = self.embed_text(verb) if verb and verb != "None" else None
            object_emb = self.embed_text(self._token_to_sentence(object_text)) if object_text and object_text not in ("None", "none", "") else None
            
            return subject_emb, verb_emb, object_emb


class RGCNModel(torch.nn.Module):
    """
    R-GCN 모델 정의 (학습 코드와 동일)
    """
    
    def __init__(self, num_rel: int, in_dim: int, hidden: int, out_dim: int, 
                 num_bases: int, hop: int, self_weight: float):
        super().__init__()
        self.self_loop_id = num_rel
        self.self_weight = self_weight
        self.convs = torch.nn.ModuleList([
            RGCNConv(in_dim if i == 0 else hidden,
                     out_dim if i == hop - 1 else hidden,
                     num_rel + 1, num_bases=num_bases)
            for i in range(hop)
        ])
    
    def forward(self, x, edge_index, edge_type):
        N = x.size(0)
        loop_idx = torch.arange(N, device=x.device)
        self_loops = torch.stack([loop_idx, loop_idx])
        loop_types = torch.full((N,), self.self_loop_id, dtype=torch.long, device=x.device)
        edge_index = torch.cat([edge_index, self_loops], dim=1)
        edge_type = torch.cat([edge_type, loop_types])
        out = x
        for i, conv in enumerate(self.convs):
            h = conv(out, edge_index, edge_type)
            out = self.self_weight * out + (1 - self.self_weight) * (F.relu(h) if i < len(self.convs) - 1 else h)
        return out
