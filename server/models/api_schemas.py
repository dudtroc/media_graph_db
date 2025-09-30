"""
API Request/Response 스키마 정의
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class VideoCreate(BaseModel):
    """비디오 생성 요청 스키마"""
    video_unique_id: int
    drama_name: str
    episode_number: str

class SceneCreate(BaseModel):
    """장면 생성 요청 스키마"""
    video_unique_id: int
    scene_data: Dict[str, Any]
    pt_data: Optional[Dict[str, Any]] = None

class SearchQuery(BaseModel):
    """하이브리드 검색 요청 스키마"""
    query_text: str
    query_embedding: List[float]
    node_type: Optional[str] = None
    top_k: int = 5

class VectorSearchQuery(BaseModel):
    """벡터 검색 요청 스키마"""
    query_embedding: Optional[List[float]] = None
    node_type: str
    top_k: int = 5
    scene_id: Optional[int] = None
    specific_node_id: Optional[str] = None
    tau: float = 0.0

class VideoResponse(BaseModel):
    """비디오 응답 스키마"""
    id: int
    video_unique_id: int
    drama_name: str
    episode_number: str
    created_at: str
    updated_at: str

class SceneResponse(BaseModel):
    """장면 응답 스키마"""
    id: int
    video_id: int
    scene_number: str
    scene_place: Optional[str]
    scene_time: Optional[str]
    scene_atmosphere: Optional[str]
    start_frame: Optional[int]
    end_frame: Optional[int]
    created_at: str

class SearchResult(BaseModel):
    """검색 결과 스키마"""
    node_type: str
    id: int
    label: str
    similarity: float
    scene_number: str
    drama_name: str
    episode_number: str


