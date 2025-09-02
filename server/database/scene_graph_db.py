#!/usr/bin/env python3
"""
PostgreSQL + pgvector를 이용한 장면 그래프 데이터베이스 클래스
새로운 스키마 구조에 맞게 설계됨
"""

import os
import json
import torch
import psycopg2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

class SceneGraphDatabase:
    """
    PostgreSQL + pgvector를 이용한 장면 그래프 데이터베이스 클래스
    새로운 스키마 구조: VIDEO → SCENES → NODES → EMBEDDINGS
    """
    
    def __init__(self, db_config: Dict[str, str] = None):
        """
        데이터베이스 연결 초기화
        
        Args:
            db_config: 데이터베이스 연결 설정
        """
        if db_config is None:
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'database': os.getenv('DB_NAME', 'scene_graph_db'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password'),
                'port': os.getenv('DB_PORT', '5432')
            }
        
        self.db_config = db_config
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ PostgreSQL 데이터베이스 연결 성공")
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    def create_tables(self):
        """필요한 테이블들을 생성"""
        from models.database_schemas import (
            CREATE_TABLES_SQL, 
            CREATE_INDEXES_SQL, 
            CREATE_VECTOR_INDEXES_SQL
        )
        
        with self.conn.cursor() as cur:
            # 테이블 생성
            cur.execute(CREATE_TABLES_SQL)
            
            # 기본 인덱스 생성
            cur.execute(CREATE_INDEXES_SQL)
            
            # 벡터 검색 인덱스 (pgvector 확장 필요)
            try:
                cur.execute(CREATE_VECTOR_INDEXES_SQL)
                print("✅ pgvector 인덱스 생성 완료")
            except Exception as e:
                print(f"⚠️ pgvector 인덱스 생성 실패 (확장이 설치되지 않음): {e}")
            
            self.conn.commit()
            print("✅ 테이블 및 인덱스 생성 완료")
    
    def insert_video_data(self, video_unique_id: int, drama_name: str, episode_number: str) -> int:
        """
        비디오 데이터 삽입
        
        Args:
            video_unique_id: 다른 DB와 연결할 고유 번호
            drama_name: 드라마 이름
            episode_number: 에피소드 번호
            
        Returns:
            int: 삽입된 비디오의 ID
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO video (video_unique_id, drama_name, episode_number)
                VALUES (%s, %s, %s)
                ON CONFLICT (video_unique_id) DO UPDATE SET
                    drama_name = EXCLUDED.drama_name,
                    episode_number = EXCLUDED.episode_number,
                    updated_at = NOW()
                RETURNING id
            """, (video_unique_id, drama_name, episode_number))
            
            video_id = cur.fetchone()[0]
            self.conn.commit()
            print(f"✅ 비디오 데이터 삽입 완료: {drama_name} {episode_number} (ID: {video_id})")
            return video_id
    
    def insert_scene_data(self, video_id: int, scene_data: dict, pt_data: dict = None) -> int:
        """
        장면 데이터를 데이터베이스에 삽입
        
        Args:
            video_id: 비디오 ID
            scene_data: API 스키마에 맞는 장면 데이터
            pt_data: PT 파일의 임베딩 데이터 (선택사항)
            
        Returns:
            int: 삽입된 장면의 ID
        """
        with self.conn.cursor() as cur:
            # 1. 장면 메타데이터 삽입
            scene_number = scene_data.get('scene_number', 'unknown')
            scene_place = scene_data.get('scene_place')
            scene_time = scene_data.get('scene_time')
            scene_atmosphere = scene_data.get('scene_atmosphere')
            start_frame = scene_data.get('start_frame')
            end_frame = scene_data.get('end_frame')
            
            cur.execute("""
                INSERT INTO scenes (video_id, scene_number, scene_place, scene_time, scene_atmosphere, start_frame, end_frame)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (video_id, scene_number) DO UPDATE SET
                    scene_place = EXCLUDED.scene_place,
                    scene_time = EXCLUDED.scene_time,
                    scene_atmosphere = EXCLUDED.scene_atmosphere,
                    start_frame = EXCLUDED.start_frame,
                    end_frame = EXCLUDED.end_frame
                RETURNING id
            """, (video_id, scene_number, scene_place, scene_time, scene_atmosphere, start_frame, end_frame))
            
            scene_db_id = cur.fetchone()[0]
            
            # pt_data가 있고 scene_graph 정보가 포함된 경우에만 노드 데이터 삽입
            print(f"🔍 pt_data 확인: {pt_data is not None}")
            if pt_data:
                print(f"🔍 pt_data 키들: {list(pt_data.keys()) if pt_data else 'None'}")
            
            if pt_data and 'scene_graph' in pt_data:
                scene_graph_data = pt_data['scene_graph']
                
                # 2. 객체 노드 삽입
                for obj in scene_graph_data.get('objects', []):
                    cur.execute("""
                        INSERT INTO objects (scene_id, object_id, super_type, type_of, label, attributes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (scene_id, object_id) DO UPDATE SET
                            super_type = EXCLUDED.super_type,
                            type_of = EXCLUDED.type_of,
                            label = EXCLUDED.label,
                            attributes = EXCLUDED.attributes
                    """, (
                        scene_db_id,
                        obj['object_id'],
                        obj['super_type'],
                        obj['type of'],
                        obj['label'],
                        json.dumps(obj.get('attributes', {}))
                    ))
                
                # 3. 이벤트 노드 삽입
                for event in scene_graph_data.get('events', []):
                    cur.execute("""
                        INSERT INTO events (scene_id, event_id, subject_id, verb, object_id, attributes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (scene_id, event_id) DO UPDATE SET
                            subject_id = EXCLUDED.subject_id,
                            verb = EXCLUDED.verb,
                            object_id = EXCLUDED.object_id,
                            attributes = EXCLUDED.attributes
                    """, (
                        scene_db_id,
                        event['event_id'],
                        event['subject'],
                        event['verb'],
                        event.get('object'),
                        json.dumps({'attribute': event.get('attribute', '')})
                    ))
                
                # 4. 공간 관계 삽입
                for spatial in scene_graph_data.get('spatial', []):
                    cur.execute("""
                        INSERT INTO spatial (scene_id, spatial_id, subject_id, predicate, object_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (scene_id, spatial_id) DO UPDATE SET
                            subject_id = EXCLUDED.subject_id,
                            predicate = EXCLUDED.predicate,
                            object_id = EXCLUDED.object_id
                    """, (
                        scene_db_id,
                        spatial['spatial_id'],
                        spatial['subject'],
                        spatial['predicate'],
                        spatial['object']
                    ))
                
                # 5. 시간 관계 삽입
                for temporal in scene_graph_data.get('temporal', []):
                    cur.execute("""
                        INSERT INTO temporal (scene_id, temporal_id, subject_id, predicate, object_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (scene_id, temporal_id) DO UPDATE SET
                            subject_id = EXCLUDED.subject_id,
                            predicate = EXCLUDED.predicate,
                            object_id = EXCLUDED.object_id
                    """, (
                        scene_db_id,
                        temporal['temporal_id'],
                        temporal['subject'],
                        temporal['predicate'],
                        temporal['object']
                    ))
                
                # 6. 임베딩 데이터 삽입 (pt_data에서)
                if 'z' in pt_data and 'orig_id' in pt_data:
                    print(f"🔗 임베딩 데이터 처리 중: {len(pt_data['z'])}개 벡터")
                    
                    # PyTorch 텐서를 numpy로 변환
                    if hasattr(pt_data['z'], 'numpy'):
                        embeddings = pt_data['z'].numpy()
                    else:
                        embeddings = np.array(pt_data['z'])
                    
                    orig_ids = pt_data['orig_id']
                    
                    for i, orig_id in enumerate(orig_ids):
                        # ID 0은 특별한 노드이므로 건너뛰기
                        if orig_id == 0:
                            continue
                        
                        # 노드 타입 결정 (node_type 정보 활용)
                        if 'node_type' in pt_data and i < len(pt_data['node_type']):
                            node_type_idx = pt_data['node_type'][i]
                            if node_type_idx == 0:
                                node_type = 'object'
                            elif node_type_idx == 1:
                                # 이벤트인지 공간관계인지 구분
                                if orig_id >= 3000:
                                    node_type = 'event'
                                else:
                                    node_type = 'spatial'
                            else:
                                continue
                        else:
                            # node_type 정보가 없으면 orig_id로 추정
                            if 1000 <= orig_id < 2000:
                                node_type = 'object'
                            elif 2000 <= orig_id < 3000:
                                node_type = 'temporal'
                            elif 3000 <= orig_id < 4000:
                                node_type = 'event'
                            elif 11000 <= orig_id < 12000:
                                node_type = 'spatial'
                            else:
                                continue
                        
                        # 임베딩 삽입
                        embedding = embeddings[i].tolist()
                        cur.execute("""
                            INSERT INTO embeddings (node_id, node_type, embedding)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (node_id, node_type) DO UPDATE SET
                                embedding = EXCLUDED.embedding
                        """, (orig_id, node_type, embedding))
                    
                    print(f"✅ 임베딩 데이터 저장 완료: {len(orig_ids)}개 중 {len([id for id in orig_ids if id != 0])}개 저장")
            
            self.conn.commit()
            return scene_db_id
    
    def insert_object_data(self, scene_id: int, object_id: int, super_type: str, 
                          type_of: str, label: str, attributes: dict = None) -> int:
        """객체 노드 데이터 삽입"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO objects (scene_id, object_id, super_type, type_of, label, attributes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (scene_id, object_id) DO UPDATE SET
                    super_type = EXCLUDED.super_type,
                    type_of = EXCLUDED.type_of,
                    label = EXCLUDED.label,
                    attributes = EXCLUDED.attributes
                RETURNING id
            """, (scene_id, object_id, super_type, type_of, label, 
                  json.dumps(attributes) if attributes else None))
            
            result = cur.fetchone()
            self.conn.commit()
            return result[0] if result else None
    
    def insert_event_data(self, scene_id: int, event_id: int, subject_id: int, 
                         verb: str, object_id: int = None, attributes: dict = None) -> int:
        """이벤트 노드 데이터 삽입"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO events (scene_id, event_id, subject_id, verb, object_id, attributes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (scene_id, event_id) DO UPDATE SET
                    subject_id = EXCLUDED.subject_id,
                    verb = EXCLUDED.verb,
                    object_id = EXCLUDED.object_id,
                    attributes = EXCLUDED.attributes
                RETURNING id
            """, (scene_id, event_id, subject_id, verb, object_id,
                  json.dumps(attributes) if attributes else None))
            
            result = cur.fetchone()
            self.conn.commit()
            return result[0] if result else None
    
    def insert_spatial_data(self, scene_id: int, spatial_id: int, subject_id: int, 
                           predicate: str, object_id: int) -> int:
        """공간 관계 데이터 삽입"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO spatial (scene_id, spatial_id, subject_id, predicate, object_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (scene_id, spatial_id) DO UPDATE SET
                    subject_id = EXCLUDED.subject_id,
                    predicate = EXCLUDED.predicate,
                    object_id = EXCLUDED.object_id
                RETURNING id
            """, (scene_id, spatial_id, subject_id, predicate, object_id))
            
            result = cur.fetchone()
            self.conn.commit()
            return result[0] if result else None
    
    def insert_temporal_data(self, scene_id: int, temporal_id: int, subject_id: int, 
                            predicate: str, object_id: int) -> int:
        """시간 관계 데이터 삽입"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO temporal (scene_id, temporal_id, subject_id, predicate, object_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (scene_id, temporal_id) DO UPDATE SET
                    subject_id = EXCLUDED.subject_id,
                    predicate = EXCLUDED.predicate,
                    object_id = EXCLUDED.object_id
                RETURNING id
            """, (scene_id, temporal_id, subject_id, predicate, object_id))
            
            result = cur.fetchone()
            self.conn.commit()
            return result[0] if result else None
    
    def search_similar_nodes(self, query_embedding: List[float], node_type: str, top_k: int = 5) -> List[Dict]:
        """
        특정 타입의 노드 중에서 유사한 노드를 벡터 검색으로 찾기
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            node_type: 노드 타입 ('object', 'event', 'spatial', 'temporal')
            top_k: 반환할 최대 결과 수
            
        Returns:
            List[Dict]: 검색 결과
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            if node_type == 'object':
                cur.execute("""
                    SELECT o.*, s.scene_number, v.drama_name, v.episode_number,
                           1 - (e.embedding <=> %s) as similarity
                    FROM objects o
                    JOIN scenes s ON o.scene_id = s.id
                    JOIN video v ON s.video_id = v.id
                    JOIN embeddings e ON o.object_id = e.node_id AND e.node_type = 'object'
                    ORDER BY e.embedding <=> %s
                    LIMIT %s
                """, (query_embedding, query_embedding, top_k))
            elif node_type == 'event':
                cur.execute("""
                    SELECT e.*, s.scene_number, v.drama_name, v.episode_number,
                           1 - (emb.embedding <=> %s) as similarity
                    FROM events e
                    JOIN scenes s ON e.scene_id = s.id
                    JOIN video v ON s.video_id = v.id
                    JOIN embeddings emb ON e.event_id = emb.node_id AND emb.node_type = 'event'
                    ORDER BY emb.embedding <=> %s
                    LIMIT %s
                """, (query_embedding, query_embedding, top_k))
            else:
                raise ValueError(f"지원하지 않는 노드 타입: {node_type}")
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def hybrid_search(self, query_text: str, query_embedding: List[float], 
                     node_type: str = None, top_k: int = 5) -> List[Dict]:
        """
        텍스트와 벡터를 결합한 하이브리드 검색
        
        Args:
            query_text: 검색할 텍스트
            query_embedding: 쿼리 임베딩 벡터
            node_type: 노드 타입 (None이면 모든 타입 검색)
            top_k: 반환할 최대 결과 수
            
        Returns:
            List[Dict]: 검색 결과
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            if node_type is None:
                # 모든 노드 타입에서 검색
                cur.execute("""
                    SELECT 
                        'object' as node_type,
                        o.id, o.object_id, o.super_type, o.type_of, o.label,
                        s.scene_number, v.drama_name, v.episode_number,
                        1 - (emb.embedding <=> %s) as similarity
                    FROM objects o
                    JOIN scenes s ON o.scene_id = s.id
                    JOIN video v ON s.video_id = v.id
                    JOIN embeddings emb ON o.object_id = emb.node_id AND emb.node_type = 'object'
                    WHERE o.label ILIKE %s OR o.type_of ILIKE %s
                    
                    UNION ALL
                    
                    SELECT 
                        'event' as node_type,
                        e.id, e.event_id, NULL as super_type, e.verb as type_of, 
                        CONCAT(e.verb, ' (', e.subject_id, ' -> ', COALESCE(e.object_id, 'None'), ')') as label,
                        s.scene_number, v.drama_name, v.episode_number,
                        1 - (emb.embedding <=> %s) as similarity
                    FROM events e
                    JOIN scenes s ON e.scene_id = s.id
                    JOIN video v ON s.video_id = v.id
                    JOIN embeddings emb ON e.event_id = emb.node_id AND emb.node_type = 'event'
                    WHERE e.verb ILIKE %s
                    
                    ORDER BY similarity DESC
                    LIMIT %s
                """, (
                    query_embedding, f'%{query_text}%', f'%{query_text}%',
                    query_embedding, f'%{query_text}%', top_k
                ))
            else:
                # 특정 노드 타입에서만 검색
                if node_type == 'object':
                    cur.execute("""
                        SELECT o.*, s.scene_number, v.drama_name, v.episode_number,
                               1 - (emb.embedding <=> %s) as similarity
                        FROM objects o
                        JOIN scenes s ON o.scene_id = s.id
                        JOIN video v ON s.video_id = v.id
                        JOIN embeddings emb ON o.object_id = emb.node_id AND emb.node_type = 'object'
                        WHERE (o.label ILIKE %s OR o.type_of ILIKE %s)
                        ORDER BY emb.embedding <=> %s
                        LIMIT %s
                    """, (query_embedding, f'%{query_text}%', f'%{query_text}%', query_embedding, top_k))
                elif node_type == 'event':
                    cur.execute("""
                        SELECT e.*, s.scene_number, v.drama_name, v.episode_number,
                               1 - (emb.embedding <=> %s) as similarity
                        FROM events e
                        JOIN scenes s ON e.scene_id = s.id
                        JOIN video v ON s.video_id = v.id
                        JOIN embeddings emb ON e.event_id = emb.node_id AND emb.node_type = 'event'
                        WHERE e.verb ILIKE %s
                        ORDER BY emb.embedding <=> %s
                        LIMIT %s
                    """, (query_embedding, f'%{query_text}%', query_embedding, top_k))
                else:
                    raise ValueError(f"지원하지 않는 노드 타입: {node_type}")
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def get_scene_graph(self, scene_id: int) -> Dict[str, Any]:
        """
        특정 장면의 전체 그래프 정보 조회 (외래키 활용)
        
        Args:
            scene_id: 장면 ID
            
        Returns:
            Dict[str, Any]: 장면 그래프 정보
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 장면 메타데이터
            cur.execute("""
                SELECT s.*, v.drama_name, v.episode_number, v.video_unique_id
                FROM scenes s
                JOIN video v ON s.video_id = v.id
                WHERE s.id = %s
            """, (scene_id,))
            scene = cur.fetchone()
            if not scene:
                return None
            
            # 객체들
            cur.execute("SELECT * FROM objects WHERE scene_id = %s ORDER BY object_id", (scene_id,))
            objects = [dict(row) for row in cur.fetchall()]
            
            # 이벤트들
            cur.execute("SELECT * FROM events WHERE scene_id = %s ORDER BY event_id", (scene_id,))
            events = [dict(row) for row in cur.fetchall()]
            
            # 공간 관계들
            cur.execute("SELECT * FROM spatial WHERE scene_id = %s ORDER BY spatial_id", (scene_id,))
            spatial = [dict(row) for row in cur.fetchall()]
            
            # 시간 관계들
            cur.execute("SELECT * FROM temporal WHERE scene_id = %s ORDER BY temporal_id", (scene_id,))
            temporal = [dict(row) for row in cur.fetchall()]
            
            return {
                'scene': dict(scene),
                'objects': objects,
                'events': events,
                'spatial': spatial,
                'temporal': temporal
            }
    
    def get_video_summary(self, video_unique_id: int) -> Dict[str, Any]:
        """
        특정 비디오의 요약 정보 조회
        
        Args:
            video_unique_id: 비디오 고유 번호
            
        Returns:
            Dict[str, Any]: 비디오 요약 정보
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT v.*, 
                       COUNT(s.id) as scene_count,
                       COUNT(DISTINCT o.id) as object_count,
                       COUNT(DISTINCT e.id) as event_count,
                       COUNT(DISTINCT sp.id) as spatial_count,
                       COUNT(DISTINCT t.id) as temporal_count
                FROM video v
                LEFT JOIN scenes s ON v.id = s.video_id
                LEFT JOIN objects o ON s.id = o.scene_id
                LEFT JOIN events e ON s.id = e.scene_id
                LEFT JOIN spatial sp ON s.id = sp.scene_id
                LEFT JOIN temporal t ON s.id = t.scene_id
                WHERE v.video_unique_id = %s
                GROUP BY v.id
            """, (video_unique_id,))
            
            result = cur.fetchone()
            return dict(result) if result else None
    
    def get_video_by_name_episode(self, drama_name: str, episode_number: str) -> Optional[Dict[str, Any]]:
        """
        드라마 이름과 에피소드 번호로 비디오 조회
        
        Args:
            drama_name: 드라마 이름
            episode_number: 에피소드 번호
            
        Returns:
            Dict[str, Any]: 비디오 정보 또는 None
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM video 
                WHERE drama_name = %s AND episode_number = %s
            """, (drama_name, episode_number))
            
            result = cur.fetchone()
            return dict(result) if result else None
    
    def safe_insert_video_data(self, video_unique_id: int, drama_name: str, episode_number: str) -> int:
        """
        안전한 비디오 데이터 삽입 (중복 체크 후)
        
        Args:
            video_unique_id: 다른 DB와 연결할 고유 번호
            drama_name: 드라마 이름
            episode_number: 에피소드 번호
            
        Returns:
            int: 비디오의 ID (기존 또는 새로 생성된)
        """
        # 기존 데이터 확인
        existing_video = self.get_video_by_name_episode(drama_name, episode_number)
        
        if existing_video:
            print(f"ℹ️  기존 비디오 발견: {drama_name} {episode_number} (ID: {existing_video['id']})")
            return existing_video['id']
        
        # 새 데이터 삽입
        return self.insert_video_data(video_unique_id, drama_name, episode_number)
    
    def _get_video_id_by_unique_id(self, video_unique_id: int) -> Optional[int]:
        """
        video_unique_id로 video_id 조회 (내부 메서드)
        
        Args:
            video_unique_id: 비디오 고유 번호
            
        Returns:
            Optional[int]: video_id 또는 None
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM video WHERE video_unique_id = %s", (video_unique_id,))
            result = cur.fetchone()
            return result[0] if result else None
    
    def get_all_videos(self) -> List[Dict[str, Any]]:
        """
        모든 비디오 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 비디오 목록
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, video_unique_id, drama_name, episode_number, created_at, updated_at
                FROM video
                ORDER BY created_at DESC
            """)
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            print("✅ 데이터베이스 연결 종료")
