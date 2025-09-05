#!/usr/bin/env python3
"""
Scene Graph Database API Server
FastAPI를 사용한 REST API 서버
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import SceneGraphDatabaseManager
from models.api_schemas import (
    VideoCreate, SceneCreate, SearchQuery, VectorSearchQuery,
    VideoResponse, SceneResponse, SearchResult
)

# 전역 데이터베이스 매니저
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global db_manager
    
    # 시작 시 데이터베이스 매니저 초기화
    print("🚀 Scene Graph Database API 서버 시작")
    db_manager = SceneGraphDatabaseManager()
    print("✅ 데이터베이스 연결 완료")
    
    yield
    
    # 종료 시 정리
    print("🛑 Scene Graph Database API 서버 종료")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Scene Graph Database API",
    description="미디어 장면 그래프 데이터베이스를 위한 REST API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_manager() -> SceneGraphDatabaseManager:
    """데이터베이스 매니저 의존성 주입"""
    if db_manager is None:
        raise HTTPException(status_code=500, detail="데이터베이스 연결이 초기화되지 않았습니다")
    return db_manager

# === 기본 엔드포인트 ===

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Scene Graph Database API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        # 데이터베이스 연결 테스트
        session = db_manager.get_session()
        try:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            db_status = "healthy"
        finally:
            session.close()
        
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

# === 비디오 관련 엔드포인트 ===

@app.post("/videos", response_model=Dict[str, Any])
async def create_video(
    video_data: VideoCreate,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """비디오 생성 (중복 시 기존 비디오 반환)"""
    try:
        # 먼저 기존 비디오가 있는지 확인
        existing_video = db.get_video_by_drama_episode(
            video_data.drama_name, 
            video_data.episode_number
        )
        
        if existing_video:
            return {
                "success": True,
                "video_id": existing_video['id'],
                "video_unique_id": existing_video['video_unique_id'],
                "message": f"기존 비디오 '{video_data.drama_name} {video_data.episode_number}' 사용 (ID: {existing_video['id']})"
            }
        
        # 기존 비디오가 없으면 새로 생성
        video_id = db.insert_video_data(
            video_data.video_unique_id,
            video_data.drama_name,
            video_data.episode_number
        )
        return {
            "success": True,
            "video_id": video_id,
            "video_unique_id": video_data.video_unique_id,
            "message": f"비디오 '{video_data.drama_name} {video_data.episode_number}' 생성 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 생성 실패: {str(e)}")

@app.get("/videos", response_model=List[Dict[str, Any]])
async def get_videos(db: SceneGraphDatabaseManager = Depends(get_db_manager)):
    """모든 비디오 목록 조회"""
    try:
        videos = db.get_all_videos()
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 목록 조회 실패: {str(e)}")

@app.get("/videos/{video_unique_id}", response_model=Dict[str, Any])
async def get_video_with_scenes(
    video_unique_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """비디오 정보와 연결된 장면 목록 조회"""
    try:
        # 비디오 정보 조회
        videos = db.get_all_videos()
        video = next((v for v in videos if v.get('video_unique_id') == video_unique_id), None)
        
        if not video:
            raise HTTPException(status_code=404, detail="비디오를 찾을 수 없습니다")
        
        # 연결된 장면 목록 조회
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT s.id, s.scene_number, s.scene_place, s.scene_time, 
                       s.scene_atmosphere, s.start_frame, s.end_frame, s.created_at
                FROM scenes s 
                WHERE s.video_id = :video_id 
                ORDER BY s.created_at
            """), {"video_id": video['id']})
            
            scenes = []
            for row in result:
                scenes.append({
                    "scene_id": row.id,
                    "scene_number": row.scene_number,
                    "scene_place": row.scene_place,
                    "scene_time": row.scene_time,
                    "scene_atmosphere": row.scene_atmosphere,
                    "start_frame": row.start_frame,
                    "end_frame": row.end_frame,
                    "created_at": str(row.created_at)
                })
            
            return {
                "video_id": video['id'],
                "video_unique_id": video['video_unique_id'],
                "drama_name": video['drama_name'],
                "episode_number": video['episode_number'],
                "created_at": video['created_at'],
                "updated_at": video['updated_at'],
                "scenes": scenes,
                "scene_count": len(scenes)
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 및 장면 조회 실패: {str(e)}")

@app.get("/videos/{video_unique_id}/summary", response_model=Dict[str, Any])
async def get_video_summary(
    video_unique_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """비디오 요약 정보 조회"""
    try:
        # 비디오 정보 조회
        videos = db.get_all_videos()
        video = next((v for v in videos if v.get('video_unique_id') == video_unique_id), None)
        
        if not video:
            raise HTTPException(status_code=404, detail="비디오를 찾을 수 없습니다")
        
        # 장면 수 조회
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT COUNT(*) as scene_count
                FROM scenes s 
                WHERE s.video_id = :video_id
            """), {"video_id": video['id']})
            
            scene_count = result.fetchone().scene_count
        finally:
            session.close()
        
        return {
            "video_id": video['id'],
            "video_unique_id": video['video_unique_id'],
            "drama_name": video['drama_name'],
            "episode_number": video['episode_number'],
            "scene_count": scene_count,
            "created_at": video['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 요약 조회 실패: {str(e)}")

# === 장면 관련 엔드포인트 ===

@app.post("/scenes", response_model=Dict[str, Any])
async def create_scene(
    scene_request: SceneCreate,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """장면 데이터 생성 (임베딩 포함)"""
    try:
        # 비디오 ID 조회
        videos = db.get_all_videos()
        video = next((v for v in videos if int(v.get('video_unique_id')) == int(scene_request.video_unique_id)), None)
        
        if not video:
            raise HTTPException(status_code=404, detail="비디오를 찾을 수 없습니다")
        
        # 장면 데이터 생성
        scene_id = db.insert_scene_data(
            video['id'],
            scene_request.scene_data,
            scene_request.pt_data
        )
        
        return {
            "success": True,
            "scene_id": scene_id,
            "video_id": video['id'],
            "message": "장면 데이터 생성 완료"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장면 생성 실패: {str(e)}")

@app.get("/scenes/{scene_id}", response_model=Dict[str, Any])
async def get_scene_graph(
    scene_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """특정 장면의 완전한 그래프 정보 조회 (모든 노드와 임베딩 포함)"""
    try:
        # 장면 기본 정보 조회
        session = db.get_session()
        try:
            from sqlalchemy import text
            
            # 1. 장면 기본 정보
            scene_result = session.execute(text("""
                SELECT s.id, s.scene_number, s.scene_place, s.scene_time, 
                       s.scene_atmosphere, s.start_frame, s.end_frame, s.created_at,
                       v.drama_name, v.episode_number, v.video_unique_id
                FROM scenes s 
                JOIN video v ON s.video_id = v.id
                WHERE s.id = :scene_id
            """), {"scene_id": scene_id})
            
            scene_row = scene_result.fetchone()
            if not scene_row:
                raise HTTPException(status_code=404, detail="장면을 찾을 수 없습니다")
            
            # 2. 객체 노드들
            objects_result = session.execute(text("""
                SELECT o.id, o.object_id, o.super_type, o.type_of, 
                       o.label, o.attributes, o.created_at
                FROM objects o 
                WHERE o.scene_id = :scene_id 
                ORDER BY o.object_id
            """), {"scene_id": scene_id})
            
            objects = []
            for row in objects_result:
                objects.append({
                    "id": row.id,
                    "object_id": row.object_id,
                    "super_type": row.super_type,
                    "type_of": row.type_of,
                    "label": row.label,
                    "attributes": row.attributes,
                    "created_at": str(row.created_at)
                })
            
            # 3. 이벤트 노드들
            events_result = session.execute(text("""
                SELECT e.id, e.event_id, e.subject_id, e.verb, 
                       e.object_id, e.attributes, e.created_at
                FROM events e 
                WHERE e.scene_id = :scene_id 
                ORDER BY e.event_id
            """), {"scene_id": scene_id})
            
            events = []
            for row in events_result:
                events.append({
                    "id": row.id,
                    "event_id": row.event_id,
                    "subject_id": row.subject_id,
                    "verb": row.verb,
                    "object_id": row.object_id,
                    "attributes": row.attributes,
                    "created_at": str(row.created_at)
                })
            
            # 4. 공간관계들
            spatial_result = session.execute(text("""
                SELECT s.id, s.spatial_id, s.subject_id, s.predicate, 
                       s.object_id, s.created_at
                FROM spatial s 
                WHERE s.scene_id = :scene_id 
                ORDER BY s.spatial_id
            """), {"scene_id": scene_id})
            
            spatial = []
            for row in spatial_result:
                spatial.append({
                    "id": row.id,
                    "spatial_id": row.spatial_id,
                    "subject_id": row.subject_id,
                    "predicate": row.predicate,
                    "object_id": row.object_id,
                    "created_at": str(row.created_at)
                })
            
            # 5. 시간관계들
            temporal_result = session.execute(text("""
                SELECT t.id, t.temporal_id, t.subject_id, t.predicate, 
                       t.object_id, t.created_at
                FROM temporal t 
                WHERE t.scene_id = :scene_id 
                ORDER BY t.temporal_id
            """), {"scene_id": scene_id})
            
            temporal = []
            for row in temporal_result:
                temporal.append({
                    "id": row.id,
                    "temporal_id": row.temporal_id,
                    "subject_id": row.subject_id,
                    "predicate": row.predicate,
                    "object_id": row.object_id,
                    "created_at": str(row.created_at)
                })
            
            # 6. 임베딩 정보들
            embeddings_result = session.execute(text("""
                SELECT e.id, e.node_id, e.node_type, e.embedding, e.created_at
                FROM embeddings e 
                WHERE e.node_id IN (
                    SELECT DISTINCT o.object_id FROM objects o WHERE o.scene_id = :scene_id
                    UNION
                    SELECT DISTINCT e2.event_id FROM events e2 WHERE e2.scene_id = :scene_id
                    UNION
                    SELECT DISTINCT s.spatial_id FROM spatial s WHERE s.scene_id = :scene_id
                    UNION
                    SELECT DISTINCT t.temporal_id FROM temporal t WHERE t.scene_id = :scene_id
                )
                ORDER BY e.node_type, e.node_id
            """), {"scene_id": scene_id})
            
            embeddings = []
            for row in embeddings_result:
                embedding_vector = row.embedding
                vector_length = len(embedding_vector) if embedding_vector else 0
                embeddings.append({
                    "id": row.id,
                    "node_id": row.node_id,
                    "node_type": row.node_type,
                    "embedding": embedding_vector,
                    "vector_length": vector_length,
                    "created_at": str(row.created_at)
                })
            
            # 완전한 장면 그래프 정보 반환
            return {
                "scene": {
                    "id": scene_row.id,
                    "scene_number": scene_row.scene_number,
                    "scene_place": scene_row.scene_place,
                    "scene_time": scene_row.scene_time,
                    "scene_atmosphere": scene_row.scene_atmosphere,
                    "start_frame": scene_row.start_frame,
                    "end_frame": scene_row.end_frame,
                    "created_at": str(scene_row.created_at),
                    "drama_name": scene_row.drama_name,
                    "episode_number": scene_row.episode_number,
                    "video_unique_id": scene_row.video_unique_id
                },
                "objects": objects,
                "events": events,
                "spatial": spatial,
                "temporal": temporal,
                "embeddings": embeddings,
                "summary": {
                    "total_objects": len(objects),
                    "total_events": len(events),
                    "total_spatial": len(spatial),
                    "total_temporal": len(temporal),
                    "total_embeddings": len(embeddings)
                }
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장면 그래프 조회 실패: {str(e)}")

@app.get("/videos/{video_id}/scenes", response_model=List[Dict[str, Any]])
async def get_video_scenes(
    video_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """특정 비디오의 장면 목록 조회"""
    try:
        # 비디오 존재 확인
        videos = db.get_all_videos()
        video = next((v for v in videos if v['id'] == video_id), None)
        if not video:
            raise HTTPException(status_code=404, detail="비디오를 찾을 수 없습니다")
        
        # 장면 목록 조회
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT s.id, s.scene_number, s.scene_place, s.scene_time, 
                       s.scene_atmosphere, s.start_frame, s.end_frame, s.created_at
                FROM scenes s 
                WHERE s.video_id = :video_id 
                ORDER BY s.created_at
            """), {"video_id": video_id})
            
            scenes = []
            for row in result:
                scenes.append({
                    "id": row.id,
                    "scene_number": row.scene_number,
                    "scene_place": row.scene_place,
                    "scene_time": row.scene_time,
                    "scene_atmosphere": row.scene_atmosphere,
                    "start_frame": row.start_frame,
                    "end_frame": row.end_frame,
                    "created_at": str(row.created_at)
                })
            
            return scenes
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장면 목록 조회 실패: {str(e)}")

@app.get("/scenes/{scene_id}/objects", response_model=List[Dict[str, Any]])
async def get_scene_objects(
    scene_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """특정 장면의 객체 노드 조회"""
    try:
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT o.id, o.object_id, o.super_type, o.type_of, 
                       o.label, o.attributes, o.created_at
                FROM objects o 
                WHERE o.scene_id = :scene_id 
                ORDER BY o.object_id
            """), {"scene_id": scene_id})
            
            objects = []
            for row in result:
                objects.append({
                    "id": row.id,
                    "object_id": row.object_id,
                    "super_type": row.super_type,
                    "type_of": row.type_of,
                    "label": row.label,
                    "attributes": row.attributes,
                    "created_at": str(row.created_at)
                })
            
            return objects
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"객체 노드 조회 실패: {str(e)}")

@app.get("/scenes/{scene_id}/events", response_model=List[Dict[str, Any]])
async def get_scene_events(
    scene_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """특정 장면의 이벤트 노드 조회"""
    try:
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT e.id, e.event_id, e.subject_id, e.verb, 
                       e.object_id, e.attributes, e.created_at
                FROM events e 
                WHERE e.scene_id = :scene_id 
                ORDER BY e.event_id
            """), {"scene_id": scene_id})
            
            events = []
            for row in result:
                events.append({
                    "id": row.id,
                    "event_id": row.event_id,
                    "subject_id": row.subject_id,
                    "verb": row.verb,
                    "object_id": row.object_id,
                    "attributes": row.attributes,
                    "created_at": str(row.created_at)
                })
            
            return events
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이벤트 노드 조회 실패: {str(e)}")

@app.get("/scenes/{scene_id}/spatial", response_model=List[Dict[str, Any]])
async def get_scene_spatial(
    scene_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """특정 장면의 공간관계 조회"""
    try:
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT s.id, s.spatial_id, s.subject_id, s.predicate, 
                       s.object_id, s.created_at
                FROM spatial s 
                WHERE s.scene_id = :scene_id 
                ORDER BY s.spatial_id
            """), {"scene_id": scene_id})
            
            spatial = []
            for row in result:
                spatial.append({
                    "id": row.id,
                    "spatial_id": row.spatial_id,
                    "subject_id": row.subject_id,
                    "predicate": row.predicate,
                    "object_id": row.object_id,
                    "created_at": str(row.created_at)
                })
            
            return spatial
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"공간관계 조회 실패: {str(e)}")

@app.get("/scenes/{scene_id}/temporal", response_model=List[Dict[str, Any]])
async def get_scene_temporal(
    scene_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """특정 장면의 시간관계 조회"""
    try:
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT t.id, t.temporal_id, t.subject_id, t.predicate, 
                       t.object_id, t.created_at
                FROM temporal t 
                WHERE t.scene_id = :scene_id 
                ORDER BY t.temporal_id
            """), {"scene_id": scene_id})
            
            temporal = []
            for row in result:
                temporal.append({
                    "id": row.id,
                    "temporal_id": row.temporal_id,
                    "subject_id": row.subject_id,
                    "predicate": row.predicate,
                    "object_id": row.object_id,
                    "created_at": str(row.created_at)
                })
            
            return temporal
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시간관계 조회 실패: {str(e)}")

@app.get("/scenes/{scene_id}/embeddings", response_model=List[Dict[str, Any]])
async def get_scene_embeddings(
    scene_id: int,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """특정 장면의 임베딩 정보 조회"""
    try:
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT e.id, e.node_id, e.node_type, e.embedding, e.created_at
                FROM embeddings e 
                WHERE e.node_id IN (
                    SELECT DISTINCT o.object_id FROM objects o WHERE o.scene_id = :scene_id
                    UNION
                    SELECT DISTINCT e2.event_id FROM events e2 WHERE e2.scene_id = :scene_id
                    UNION
                    SELECT DISTINCT s.spatial_id FROM spatial s WHERE s.scene_id = :scene_id
                    UNION
                    SELECT DISTINCT t.temporal_id FROM temporal t WHERE t.scene_id = :scene_id
                )
                ORDER BY e.node_type, e.node_id
            """), {"scene_id": scene_id})
            
            embeddings = []
            for row in result:
                embedding_vector = row.embedding
                vector_length = len(embedding_vector) if embedding_vector else 0
                embeddings.append({
                    "id": row.id,
                    "node_id": row.node_id,
                    "node_type": row.node_type,
                    "embedding": embedding_vector,
                    "vector_length": vector_length,
                    "created_at": str(row.created_at)
                })
            
            return embeddings
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임베딩 정보 조회 실패: {str(e)}")

# === 검색 관련 엔드포인트 ===

@app.post("/search/vector", response_model=List[Dict[str, Any]])
async def vector_search(
    search_query: VectorSearchQuery,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """벡터 기반 유사도 검색"""
    try:
        results = db.search_similar_nodes(
            search_query.query_embedding,
            search_query.node_type,
            search_query.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벡터 검색 실패: {str(e)}")

@app.post("/search/hybrid", response_model=List[Dict[str, Any]])
async def hybrid_search(
    search_query: SearchQuery,
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """하이브리드 검색 (텍스트 + 벡터)"""
    try:
        # TODO: 하이브리드 검색 구현
        # 현재는 벡터 검색만 수행
        results = db.search_similar_nodes(
            search_query.query_embedding,
            search_query.node_type,
            search_query.top_k
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"하이브리드 검색 실패: {str(e)}")

# === 노드 관련 엔드포인트 ===

@app.post("/objects", response_model=Dict[str, Any])
async def create_object(
    object_data: Dict[str, Any],
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """객체 노드 생성"""
    try:
        object_id = db.insert_object_data(
            scene_id=object_data['scene_id'],
            object_id=object_data['object_id'],
            super_type=object_data['super_type'],
            type_of=object_data['type_of'],
            label=object_data['label'],
            attributes=object_data.get('attributes', {})
        )
        return {
            "success": True,
            "object_id": object_id,
            "message": "객체 노드 생성 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"객체 생성 실패: {str(e)}")

@app.post("/events", response_model=Dict[str, Any])
async def create_event(
    event_data: Dict[str, Any],
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """이벤트 노드 생성"""
    try:
        event_id = db.insert_event_data(
            scene_id=event_data['scene_id'],
            event_id=event_data['event_id'],
            subject_id=event_data['subject_id'],
            verb=event_data['verb'],
            object_id=event_data.get('object_id'),
            attributes=event_data.get('attributes', {})
        )
        return {
            "success": True,
            "event_id": event_id,
            "message": "이벤트 노드 생성 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이벤트 생성 실패: {str(e)}")

@app.post("/spatial", response_model=Dict[str, Any])
async def create_spatial(
    spatial_data: Dict[str, Any],
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """공간 관계 생성"""
    try:
        spatial_id = db.insert_spatial_data(
            scene_id=spatial_data['scene_id'],
            spatial_id=spatial_data['spatial_id'],
            subject_id=spatial_data['subject_id'],
            predicate=spatial_data['predicate'],
            object_id=spatial_data['object_id']
        )
        return {
            "success": True,
            "spatial_id": spatial_id,
            "message": "공간 관계 생성 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"공간 관계 생성 실패: {str(e)}")

@app.post("/temporal", response_model=Dict[str, Any])
async def create_temporal(
    temporal_data: Dict[str, Any],
    db: SceneGraphDatabaseManager = Depends(get_db_manager)
):
    """시간 관계 생성"""
    try:
        temporal_id = db.insert_temporal_data(
            scene_id=temporal_data['scene_id'],
            temporal_id=temporal_data['temporal_id'],
            subject_id=temporal_data['subject_id'],
            predicate=temporal_data['predicate'],
            object_id=temporal_data['object_id']
        )
        return {
            "success": True,
            "temporal_id": temporal_id,
            "message": "시간 관계 생성 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시간 관계 생성 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
