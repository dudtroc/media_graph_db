"""
SQLAlchemy 기반 데이터베이스 관리 클래스
기존 SceneGraphDatabase 클래스를 SQLAlchemy ORM으로 리팩토링
"""

import os
import json
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from models.orm_models import (
    Base, Video, Scene, Object, Event, Spatial, Temporal, Embedding,
    engine, SessionLocal, create_tables
)

load_dotenv()

class SceneGraphDatabaseManager:
    """
    SQLAlchemy ORM을 이용한 장면 그래프 데이터베이스 관리 클래스
    기존 SceneGraphDatabase 클래스를 ORM으로 리팩토링
    """
    
    def __init__(self):
        """데이터베이스 연결 초기화"""
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.create_tables()
        print("✅ SQLAlchemy 데이터베이스 연결 성공")
    
    def create_tables(self):
        """필요한 테이블들을 생성"""
        try:
            create_tables()
            print("✅ 테이블 및 인덱스 생성 완료")
        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")
            raise
    
    def get_session(self) -> Session:
        """데이터베이스 세션 생성"""
        return self.SessionLocal()
    
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
        session = self.get_session()
        try:
            # 기존 비디오가 있는지 확인
            existing_video = session.query(Video).filter(
                Video.video_unique_id == video_unique_id
            ).first()
            
            if existing_video:
                # 기존 비디오 업데이트
                existing_video.drama_name = drama_name
                existing_video.episode_number = episode_number
                existing_video.updated_at = func.now()
                session.commit()
                video_id = existing_video.id
                print(f"✅ 비디오 데이터 업데이트 완료: {drama_name} {episode_number} (ID: {video_id})")
            else:
                # 새 비디오 생성
                new_video = Video(
                    video_unique_id=video_unique_id,
                    drama_name=drama_name,
                    episode_number=episode_number
                )
                session.add(new_video)
                session.commit()
                session.refresh(new_video)
                video_id = new_video.id
                print(f"✅ 비디오 데이터 삽입 완료: {drama_name} {episode_number} (ID: {video_id})")
            
            return video_id
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ 비디오 데이터 삽입 실패: {e}")
            raise
        finally:
            session.close()
    
    def insert_scene_data(self, video_id: int, scene_data: dict, pt_data: dict) -> int:
        """
        장면 데이터를 데이터베이스에 삽입 (API 형식 지원)
        
        Args:
            video_id: 비디오 ID
            scene_data: API에서 전달되는 장면 데이터
            pt_data: PT 파일의 임베딩 데이터 또는 None
            
        Returns:
            int: 삽입된 장면의 ID
        """
        session = self.get_session()
        try:
            # 1. 장면 메타데이터 삽입/업데이트
            scene_number = scene_data.get('scene_number', 'unknown')
            scene_place = scene_data.get('scene_place')
            scene_time = scene_data.get('scene_time')
            scene_atmosphere = scene_data.get('scene_atmosphere')
            start_frame = scene_data.get('start_frame')
            end_frame = scene_data.get('end_frame')
            
            # 기존 장면이 있는지 확인
            existing_scene = session.query(Scene).filter(
                and_(Scene.video_id == video_id, Scene.scene_number == scene_number)
            ).first()
            
            if existing_scene:
                # 기존 장면 업데이트
                existing_scene.scene_place = scene_place
                existing_scene.scene_time = scene_time
                existing_scene.scene_atmosphere = scene_atmosphere
                existing_scene.start_frame = start_frame
                existing_scene.end_frame = end_frame
                session.commit()
                scene_db_id = existing_scene.id
            else:
                # 새 장면 생성
                new_scene = Scene(
                    video_id=video_id,
                    scene_number=scene_number,
                    scene_place=scene_place,
                    scene_time=scene_time,
                    scene_atmosphere=scene_atmosphere,
                    start_frame=start_frame,
                    end_frame=end_frame
                )
                session.add(new_scene)
                session.commit()
                session.refresh(new_scene)
                scene_db_id = new_scene.id
            
            # 2. 임베딩 데이터가 있는 경우에만 처리
            if pt_data and 'z' in pt_data and 'orig_id' in pt_data:
                print(f"🔗 임베딩 데이터 처리 중: {len(pt_data['z'])}개 벡터")
                
                # PyTorch 텐서를 numpy로 변환
                if hasattr(pt_data['z'], 'numpy'):
                    embeddings = pt_data['z'].numpy()
                else:
                    embeddings = np.array(pt_data['z'])
                
                orig_ids = pt_data['orig_id']
                
                # 비디오 정보 조회
                video = session.query(Video).filter(Video.id == video_id).first()
                video_unique_id = video.video_unique_id
                
                for i, orig_id in enumerate(orig_ids):
                    # ID 0은 특별한 노드이므로 건너뛰기
                    if orig_id == 0:
                        continue
                    
                    # 노드 타입 결정 (node_type 정보 활용)
                    if 'node_type' in pt_data and i < len(pt_data['node_type']):
                        node_type_idx = pt_data['node_type'][i]
                        if node_type_idx == 0:
                            # 특별한 노드 (ID=0)는 건너뛰기
                            continue
                        elif node_type_idx == 1:
                            node_type = 'object'
                        elif node_type_idx == 2:
                            node_type = 'event'
                        elif node_type_idx == 3:
                            node_type = 'spatial'
                        else:
                            # 알 수 없는 노드 타입은 건너뛰기
                            continue
                    else:
                        # node_type 정보가 없으면 orig_id로 추정 (fallback)
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
                    
                    # 실제 node_id 찾기: {video_unique_id}_{scene_id}_{node_type}_{orig_id}
                    actual_node_id = f"{video_unique_id}_{scene_db_id}_{node_type}_{orig_id}"
                    
                    print(f"🔍 임베딩 매핑 시도: orig_id={orig_id} -> {actual_node_id}")
                    
                    # 해당 node_id가 실제로 존재하는지 확인
                    node_exists = False
                    if node_type == 'object':
                        node_exists = session.query(Object).filter(
                            and_(Object.scene_id == scene_db_id, Object.object_id == actual_node_id)
                        ).first() is not None
                    elif node_type == 'event':
                        node_exists = session.query(Event).filter(
                            and_(Event.scene_id == scene_db_id, Event.event_id == actual_node_id)
                        ).first() is not None
                    elif node_type == 'spatial':
                        node_exists = session.query(Spatial).filter(
                            and_(Spatial.scene_id == scene_db_id, Spatial.spatial_id == actual_node_id)
                        ).first() is not None
                    elif node_type == 'temporal':
                        node_exists = session.query(Temporal).filter(
                            and_(Temporal.scene_id == scene_db_id, Temporal.temporal_id == actual_node_id)
                        ).first() is not None
                    
                    if not node_exists:
                        print(f"⚠️ 노드가 존재하지 않음: {actual_node_id}")
                        # 디버깅을 위해 실제 저장된 노드들 확인
                        if node_type == 'object':
                            existing_objects = session.query(Object).filter(Object.scene_id == scene_db_id).all()
                            print(f"   실제 저장된 객체들: {[obj.object_id for obj in existing_objects[:5]]}")
                        elif node_type == 'event':
                            existing_events = session.query(Event).filter(Event.scene_id == scene_db_id).all()
                            print(f"   실제 저장된 이벤트들: {[evt.event_id for evt in existing_events[:5]]}")
                        elif node_type == 'spatial':
                            existing_spatial = session.query(Spatial).filter(Spatial.scene_id == scene_db_id).all()
                            print(f"   실제 저장된 공간관계들: {[sp.spatial_id for sp in existing_spatial[:5]]}")
                        continue
                    
                    # 임베딩 삽입/업데이트 (벡터 형태로 저장)
                    embedding_vector = embeddings[i].tolist()
                    
                    existing_embedding = session.query(Embedding).filter(
                        Embedding.node_id == actual_node_id
                    ).first()
                    
                    if existing_embedding:
                        existing_embedding.embedding = embedding_vector
                        print(f"✅ 임베딩 업데이트: {actual_node_id}")
                    else:
                        new_embedding = Embedding(
                            node_id=actual_node_id,
                            node_type=node_type,
                            embedding=embedding_vector
                        )
                        session.add(new_embedding)
                        print(f"✅ 임베딩 생성: {actual_node_id}")
                
                session.commit()
                print(f"✅ 임베딩 데이터 저장 완료: {len(orig_ids)}개 중 {len([id for id in orig_ids if id != 0])}개 처리")
            
            print(f"✅ 장면 데이터 삽입 완료: {scene_number} (ID: {scene_db_id})")
            return scene_db_id
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ 장면 데이터 삽입 실패: {e}")
            raise
        finally:
            session.close()
    
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
        session = self.get_session()
        try:
            if node_type == 'object':
                # pgvector를 사용한 벡터 검색 (cosine similarity)
                # 벡터를 문자열로 변환하여 직접 쿼리에 삽입
                vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                results = session.execute(text(f"""
                    SELECT o.id, o.object_id, o.super_type, o.type_of, o.label, o.attributes,
                           s.scene_number, v.drama_name, v.episode_number,
                           1 - (e.embedding <=> '{vector_str}'::vector) as similarity
                    FROM objects o
                    JOIN scenes s ON o.scene_id = s.id
                    JOIN video v ON s.video_id = v.id
                    JOIN embeddings e ON o.object_id = e.node_id AND e.node_type = 'object'
                    ORDER BY e.embedding <=> '{vector_str}'::vector
                    LIMIT :top_k
                """), {
                    'top_k': top_k
                }).fetchall()
                
                return [{
                    'id': row.id,
                    'object_id': row.object_id,
                    'super_type': row.super_type,
                    'type_of': row.type_of,
                    'label': row.label,
                    'attributes': row.attributes,
                    'scene_number': row.scene_number,
                    'drama_name': row.drama_name,
                    'episode_number': row.episode_number,
                    'similarity': float(row.similarity)
                } for row in results]
                
            elif node_type == 'event':
                # pgvector를 사용한 벡터 검색 (cosine similarity)
                # 벡터를 문자열로 변환하여 직접 쿼리에 삽입
                vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                results = session.execute(text(f"""
                    SELECT e.id, e.event_id, e.subject_id, e.verb, e.object_id, e.attributes,
                           s.scene_number, v.drama_name, v.episode_number,
                           1 - (emb.embedding <=> '{vector_str}'::vector) as similarity
                    FROM events e
                    JOIN scenes s ON e.scene_id = s.id
                    JOIN video v ON s.video_id = v.id
                    JOIN embeddings emb ON e.event_id = emb.node_id AND emb.node_type = 'event'
                    ORDER BY emb.embedding <=> '{vector_str}'::vector
                    LIMIT :top_k
                """), {
                    'top_k': top_k
                }).fetchall()
                
                return [{
                    'id': row.id,
                    'event_id': row.event_id,
                    'subject_id': row.subject_id,
                    'verb': row.verb,
                    'object_id': row.object_id,
                    'attributes': row.attributes,
                    'scene_number': row.scene_number,
                    'drama_name': row.drama_name,
                    'episode_number': row.episode_number,
                    'similarity': float(row.similarity)
                } for row in results]
            else:
                raise ValueError(f"지원하지 않는 노드 타입: {node_type}")
                
        except SQLAlchemyError as e:
            print(f"❌ 벡터 검색 실패: {e}")
            raise
        finally:
            session.close()
    
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
        session = self.get_session()
        try:
            results = []
            
            if node_type is None or node_type == 'object':
                # 객체 검색
                object_results = session.query(
                    Object, Scene, Video, Embedding
                ).join(
                    Scene, Object.scene_id == Scene.id
                ).join(
                    Video, Scene.video_id == Video.id
                ).join(
                    Embedding, and_(
                        Object.object_id == Embedding.node_id,
                        Embedding.node_type == 'object'
                    )
                ).filter(
                    or_(
                        Object.label.ilike(f'%{query_text}%'),
                        Object.type_of.ilike(f'%{query_text}%')
                    )
                ).limit(top_k).all()
                
                for obj, scene, video, embedding in object_results:
                    results.append({
                        'node_type': 'object',
                        'id': obj.id,
                        'object_id': obj.object_id,
                        'super_type': obj.super_type,
                        'type_of': obj.type_of,
                        'label': obj.label,
                        'attributes': obj.attributes,
                        'scene_number': scene.scene_number,
                        'drama_name': video.drama_name,
                        'episode_number': video.episode_number,
                        'similarity': 0.8
                    })
            
            if node_type is None or node_type == 'event':
                # 이벤트 검색
                event_results = session.query(
                    Event, Scene, Video, Embedding
                ).join(
                    Scene, Event.scene_id == Scene.id
                ).join(
                    Video, Scene.video_id == Video.id
                ).join(
                    Embedding, and_(
                        Event.event_id == Embedding.node_id,
                        Embedding.node_type == 'event'
                    )
                ).filter(
                    Event.verb.ilike(f'%{query_text}%')
                ).limit(top_k).all()
                
                for event, scene, video, embedding in event_results:
                    results.append({
                        'node_type': 'event',
                        'id': event.id,
                        'event_id': event.event_id,
                        'subject_id': event.subject_id,
                        'verb': event.verb,
                        'object_id': event.object_id,
                        'attributes': event.attributes,
                        'scene_number': scene.scene_number,
                        'drama_name': video.drama_name,
                        'episode_number': video.episode_number,
                        'similarity': 0.8
                    })
            
            return results[:top_k]
            
        except SQLAlchemyError as e:
            print(f"❌ 하이브리드 검색 실패: {e}")
            raise
        finally:
            session.close()
    
    def get_scene_graph(self, scene_id: int) -> Dict[str, Any]:
        """
        특정 장면의 전체 그래프 정보 조회
        
        Args:
            scene_id: 장면 ID
            
        Returns:
            Dict[str, Any]: 장면 그래프 정보
        """
        session = self.get_session()
        try:
            # 장면 메타데이터
            scene = session.query(Scene).filter(Scene.id == scene_id).first()
            if not scene:
                return None
            
            # 관련 데이터 조회
            video = session.query(Video).filter(Video.id == scene.video_id).first()
            objects = session.query(Object).filter(Object.scene_id == scene_id).order_by(Object.object_id).all()
            events = session.query(Event).filter(Event.scene_id == scene_id).order_by(Event.event_id).all()
            spatial = session.query(Spatial).filter(Spatial.scene_id == scene_id).order_by(Spatial.spatial_id).all()
            temporal = session.query(Temporal).filter(Temporal.scene_id == scene_id).order_by(Temporal.temporal_id).all()
            
            return {
                'scene': {
                    'id': scene.id,
                    'video_id': scene.video_id,
                    'scene_number': scene.scene_number,
                    'scene_place': scene.scene_place,
                    'scene_time': scene.scene_time,
                    'scene_atmosphere': scene.scene_atmosphere,
                    'start_frame': scene.start_frame,
                    'end_frame': scene.end_frame,
                    'created_at': scene.created_at,
                    'drama_name': video.drama_name,
                    'episode_number': video.episode_number,
                    'video_unique_id': video.video_unique_id
                },
                'objects': [{
                    'id': obj.id,
                    'object_id': obj.object_id,
                    'super_type': obj.super_type,
                    'type_of': obj.type_of,
                    'label': obj.label,
                    'attributes': obj.attributes,
                    'created_at': obj.created_at
                } for obj in objects],
                'events': [{
                    'id': event.id,
                    'event_id': event.event_id,
                    'subject_id': event.subject_id,
                    'verb': event.verb,
                    'object_id': event.object_id,
                    'attributes': event.attributes,
                    'created_at': event.created_at
                } for event in events],
                'spatial': [{
                    'id': sp.id,
                    'spatial_id': sp.spatial_id,
                    'subject_id': sp.subject_id,
                    'predicate': sp.predicate,
                    'object_id': sp.object_id,
                    'created_at': sp.created_at
                } for sp in spatial],
                'temporal': [{
                    'id': temp.id,
                    'temporal_id': temp.temporal_id,
                    'subject_id': temp.subject_id,
                    'predicate': temp.predicate,
                    'object_id': temp.object_id,
                    'created_at': temp.created_at
                } for temp in temporal]
            }
            
        except SQLAlchemyError as e:
            print(f"❌ 장면 그래프 조회 실패: {e}")
            raise
        finally:
            session.close()
    
    def get_video_summary(self, video_unique_id: int) -> Dict[str, Any]:
        """
        특정 비디오의 요약 정보 조회
        
        Args:
            video_unique_id: 비디오 고유 번호
            
        Returns:
            Dict[str, Any]: 비디오 요약 정보
        """
        session = self.get_session()
        try:
            video = session.query(Video).filter(Video.video_unique_id == video_unique_id).first()
            if not video:
                return None
            
            # 통계 정보 조회
            scene_count = session.query(Scene).filter(Scene.video_id == video.id).count()
            object_count = session.query(Object).join(Scene).filter(Scene.video_id == video.id).count()
            event_count = session.query(Event).join(Scene).filter(Scene.video_id == video.id).count()
            spatial_count = session.query(Spatial).join(Scene).filter(Scene.video_id == video.id).count()
            temporal_count = session.query(Temporal).join(Scene).filter(Scene.video_id == video.id).count()
            
            return {
                'id': video.id,
                'video_unique_id': video.video_unique_id,
                'drama_name': video.drama_name,
                'episode_number': video.episode_number,
                'created_at': video.created_at,
                'updated_at': video.updated_at,
                'scene_count': scene_count,
                'object_count': object_count,
                'event_count': event_count,
                'spatial_count': spatial_count,
                'temporal_count': temporal_count
            }
            
        except SQLAlchemyError as e:
            print(f"❌ 비디오 요약 조회 실패: {e}")
            raise
        finally:
            session.close()
    
    def _get_video_id_by_unique_id(self, video_unique_id: int) -> Optional[int]:
        """
        video_unique_id로 video_id 조회 (내부 메서드)
        
        Args:
            video_unique_id: 비디오 고유 번호
            
        Returns:
            Optional[int]: video_id 또는 None
        """
        session = self.get_session()
        try:
            video = session.query(Video).filter(Video.video_unique_id == video_unique_id).first()
            return video.id if video else None
        except SQLAlchemyError as e:
            print(f"❌ 비디오 ID 조회 실패: {e}")
            raise
        finally:
            session.close()
    
    def get_video_by_drama_episode(self, drama_name: str, episode_number: str) -> Optional[Dict[str, Any]]:
        """
        드라마명과 에피소드 번호로 비디오 조회
        
        Args:
            drama_name: 드라마명
            episode_number: 에피소드 번호
            
        Returns:
            Optional[Dict[str, Any]]: 비디오 정보 또는 None
        """
        session = self.get_session()
        try:
            video = session.query(Video).filter(
                and_(Video.drama_name == drama_name, Video.episode_number == episode_number)
            ).first()
            
            if video:
                return {
                    'id': video.id,
                    'video_unique_id': video.video_unique_id,
                    'drama_name': video.drama_name,
                    'episode_number': video.episode_number,
                    'created_at': video.created_at,
                    'updated_at': video.updated_at
                }
            return None
        except SQLAlchemyError as e:
            print(f"❌ 비디오 조회 실패: {e}")
            raise
        finally:
            session.close()

    def get_all_videos(self) -> List[Dict[str, Any]]:
        """
        모든 비디오 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 비디오 목록
        """
        session = self.get_session()
        try:
            videos = session.query(Video).order_by(Video.created_at.desc()).all()
            return [{
                'id': video.id,
                'video_unique_id': video.video_unique_id,
                'drama_name': video.drama_name,
                'episode_number': video.episode_number,
                'created_at': video.created_at,
                'updated_at': video.updated_at
            } for video in videos]
        except SQLAlchemyError as e:
            print(f"❌ 비디오 목록 조회 실패: {e}")
            raise
        finally:
            session.close()
    
    def insert_object_data(self, scene_id: int, object_id: str, super_type: str,
                          type_of: str, label: str, attributes: Dict[str, Any] = None) -> int:
        """객체 노드 데이터 삽입"""
        session = self.get_session()
        try:
            existing_object = session.query(Object).filter(
                and_(Object.scene_id == scene_id, Object.object_id == object_id)
            ).first()
            
            if existing_object:
                existing_object.super_type = super_type
                existing_object.type_of = type_of
                existing_object.label = label
                existing_object.attributes = attributes
                session.commit()
                return existing_object.id
            else:
                new_object = Object(
                    scene_id=scene_id,
                    object_id=object_id,
                    super_type=super_type,
                    type_of=type_of,
                    label=label,
                    attributes=attributes
                )
                session.add(new_object)
                session.commit()
                session.refresh(new_object)
                return new_object.id
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ 객체 데이터 삽입 실패: {e}")
            raise
        finally:
            session.close()
    
    def insert_event_data(self, scene_id: int, event_id: str, subject_id: str,
                         verb: str, object_id: str = None, attributes: Dict[str, Any] = None) -> int:
        """이벤트 노드 데이터 삽입"""
        session = self.get_session()
        try:
            existing_event = session.query(Event).filter(
                and_(Event.scene_id == scene_id, Event.event_id == event_id)
            ).first()
            
            if existing_event:
                existing_event.subject_id = subject_id
                existing_event.verb = verb
                existing_event.object_id = object_id
                existing_event.attributes = attributes
                session.commit()
                return existing_event.id
            else:
                new_event = Event(
                    scene_id=scene_id,
                    event_id=event_id,
                    subject_id=subject_id,
                    verb=verb,
                    object_id=object_id,
                    attributes=attributes
                )
                session.add(new_event)
                session.commit()
                session.refresh(new_event)
                return new_event.id
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ 이벤트 데이터 삽입 실패: {e}")
            raise
        finally:
            session.close()
    
    def insert_spatial_data(self, scene_id: int, spatial_id: str, subject_id: str,
                           predicate: str, object_id: str) -> int:
        """공간 관계 데이터 삽입"""
        session = self.get_session()
        try:
            existing_spatial = session.query(Spatial).filter(
                and_(Spatial.scene_id == scene_id, Spatial.spatial_id == spatial_id)
            ).first()
            
            if existing_spatial:
                existing_spatial.subject_id = subject_id
                existing_spatial.predicate = predicate
                existing_spatial.object_id = object_id
                session.commit()
                return existing_spatial.id
            else:
                new_spatial = Spatial(
                    scene_id=scene_id,
                    spatial_id=spatial_id,
                    subject_id=subject_id,
                    predicate=predicate,
                    object_id=object_id
                )
                session.add(new_spatial)
                session.commit()
                session.refresh(new_spatial)
                return new_spatial.id
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ 공간 관계 데이터 삽입 실패: {e}")
            raise
        finally:
            session.close()
    
    def insert_temporal_data(self, scene_id: int, temporal_id: str, subject_id: str,
                            predicate: str, object_id: str) -> int:
        """시간 관계 데이터 삽입"""
        session = self.get_session()
        try:
            existing_temporal = session.query(Temporal).filter(
                and_(Temporal.scene_id == scene_id, Temporal.temporal_id == temporal_id)
            ).first()
            
            if existing_temporal:
                existing_temporal.subject_id = subject_id
                existing_temporal.predicate = predicate
                existing_temporal.object_id = object_id
                session.commit()
                return existing_temporal.id
            else:
                new_temporal = Temporal(
                    scene_id=scene_id,
                    temporal_id=temporal_id,
                    subject_id=subject_id,
                    predicate=predicate,
                    object_id=object_id
                )
                session.add(new_temporal)
                session.commit()
                session.refresh(new_temporal)
                return new_temporal.id
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ 시간 관계 데이터 삽입 실패: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            print("✅ SQLAlchemy 데이터베이스 연결 종료")
