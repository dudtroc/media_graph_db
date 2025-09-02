#!/usr/bin/env python3
"""
FastAPI 기반 장면 그래프 데이터베이스 API 서버
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
from contextlib import asynccontextmanager

# 데이터베이스 클래스 및 모델 import
from database.scene_graph_db import SceneGraphDatabase
from models.api_schemas import VideoCreate, SceneCreate, SearchQuery, VectorSearchQuery

# 전역 데이터베이스 인스턴스
db: Optional[SceneGraphDatabase] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global db
    # 시작 시 DB 연결
    try:
        db = SceneGraphDatabase()
        print("✅ 데이터베이스 연결 성공")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        raise
    
    yield
    
    # 종료 시 DB 연결 해제
    if db:
        db.close()
        print("✅ 데이터베이스 연결 종료")

# FastAPI 앱 생성
app = FastAPI(
    title="Scene Graph Database API",
    description="미디어 장면 그래프 데이터베이스 REST API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 의존성 함수
def get_db():
    if db is None:
        raise HTTPException(status_code=500, detail="데이터베이스 연결이 설정되지 않았습니다")
    return db

# API 엔드포인트들

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Scene Graph Database API", "status": "running"}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        db_instance = get_db()
        # 간단한 쿼리로 DB 연결 상태 확인
        with db_instance.conn.cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터베이스 연결 오류: {str(e)}")

@app.post("/videos", response_model=Dict[str, Any])
async def create_video(video: VideoCreate, db_instance: SceneGraphDatabase = Depends(get_db)):
    """비디오 데이터 생성"""
    try:
        video_id = db_instance.insert_video_data(
            video.video_unique_id,
            video.drama_name,
            video.episode_number
        )
        return {
            "success": True,
            "video_id": video_id,
            "message": f"비디오 '{video.drama_name} {video.episode_number}' 생성 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 생성 실패: {str(e)}")

@app.post("/scenes", response_model=Dict[str, Any])
async def create_scene(scene: SceneCreate, db_instance: SceneGraphDatabase = Depends(get_db)):
    """장면 데이터 생성"""
    try:
        # video_unique_id로 video_id 찾기 (API를 통한 접근)
        video_id = db_instance._get_video_id_by_unique_id(scene.video_unique_id)
        if not video_id:
            raise HTTPException(status_code=404, detail="해당 video_unique_id를 찾을 수 없습니다")
        
        scene_id = db_instance.insert_scene_data(
            video_id,
            scene.scene_data,
            scene.pt_data
        )
        
        return {
            "success": True,
            "scene_id": scene_id,
            "message": f"장면 데이터 생성 완료 (ID: {scene_id})"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장면 생성 실패: {str(e)}")

@app.post("/search/vector", response_model=List[Dict[str, Any]])
async def vector_search(query: VectorSearchQuery, db_instance: SceneGraphDatabase = Depends(get_db)):
    """벡터 기반 유사도 검색"""
    try:
        results = db_instance.search_similar_nodes(
            query.query_embedding,
            query.node_type,
            query.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벡터 검색 실패: {str(e)}")

@app.post("/search/hybrid", response_model=List[Dict[str, Any]])
async def hybrid_search(query: SearchQuery, db_instance: SceneGraphDatabase = Depends(get_db)):
    """하이브리드 검색 (텍스트 + 벡터)"""
    try:
        results = db_instance.hybrid_search(
            query.query_text,
            query.query_embedding,
            query.node_type,
            query.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"하이브리드 검색 실패: {str(e)}")

@app.get("/scenes/{scene_id}", response_model=Dict[str, Any])
async def get_scene_graph(scene_id: int, db_instance: SceneGraphDatabase = Depends(get_db)):
    """특정 장면의 그래프 정보 조회"""
    try:
        scene_graph = db_instance.get_scene_graph(scene_id)
        if not scene_graph:
            raise HTTPException(status_code=404, detail="장면을 찾을 수 없습니다")
        return scene_graph
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장면 그래프 조회 실패: {str(e)}")

@app.get("/videos/{video_unique_id}/summary", response_model=Dict[str, Any])
async def get_video_summary(video_unique_id: int, db_instance: SceneGraphDatabase = Depends(get_db)):
    """비디오 요약 정보 조회"""
    try:
        summary = db_instance.get_video_summary(video_unique_id)
        if not summary:
            raise HTTPException(status_code=404, detail="비디오를 찾을 수 없습니다")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 요약 조회 실패: {str(e)}")

@app.get("/videos", response_model=List[Dict[str, Any]])
async def list_videos(db_instance: SceneGraphDatabase = Depends(get_db)):
    """모든 비디오 목록 조회"""
    try:
        videos = db_instance.get_all_videos()
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 목록 조회 실패: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
