"""
SQLAlchemy ORM 모델 정의
기존 데이터베이스 스키마를 SQLAlchemy ORM으로 변환
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    UniqueConstraint, Index, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Video(Base):
    """비디오 테이블 (드라마 + 에피소드 통합)"""
    __tablename__ = 'video'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_unique_id = Column(Integer, nullable=False, unique=True)
    drama_name = Column(String(255), nullable=False)
    episode_number = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 관계 설정
    scenes = relationship("Scene", back_populates="video", cascade="all, delete-orphan")
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('drama_name', 'episode_number', name='uq_video_drama_episode'),
        Index('idx_video_unique_id', 'video_unique_id'),
        Index('idx_video_drama_episode', 'drama_name', 'episode_number'),
    )

class Scene(Base):
    """장면 테이블"""
    __tablename__ = 'scenes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('video.id', ondelete='CASCADE'), nullable=False)
    scene_number = Column(String(255), nullable=False)
    scene_place = Column(Text)
    scene_time = Column(String(100))
    scene_atmosphere = Column(Text)
    start_frame = Column(Integer)
    end_frame = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # 관계 설정
    video = relationship("Video", back_populates="scenes")
    objects = relationship("Object", back_populates="scene", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="scene", cascade="all, delete-orphan")
    spatial_relations = relationship("Spatial", back_populates="scene", cascade="all, delete-orphan")
    temporal_relations = relationship("Temporal", back_populates="scene", cascade="all, delete-orphan")
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('video_id', 'scene_number', name='uq_scene_video_number'),
        Index('idx_scenes_video_id', 'video_id'),
    )

class Object(Base):
    """객체 노드 테이블"""
    __tablename__ = 'objects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey('scenes.id', ondelete='CASCADE'), nullable=False)
    object_id = Column(String(100), nullable=False)
    super_type = Column(String(100), nullable=False)
    type_of = Column(String(100), nullable=False)
    label = Column(Text, nullable=False)
    attributes = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    
    # 관계 설정
    scene = relationship("Scene", back_populates="objects")
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('scene_id', 'object_id', name='uq_object_scene_id'),
        Index('idx_objects_scene_id', 'scene_id'),
        Index('idx_objects_super_type', 'super_type'),
        Index('idx_objects_type_of', 'type_of'),
        Index('idx_objects_label', 'label'),
    )

class Event(Base):
    """이벤트 노드 테이블"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey('scenes.id', ondelete='CASCADE'), nullable=False)
    event_id = Column(String(100), nullable=False)
    subject_id = Column(String(100), nullable=False)
    verb = Column(String(100), nullable=False)
    object_id = Column(String(100))
    attributes = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    
    # 관계 설정
    scene = relationship("Scene", back_populates="events")
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('scene_id', 'event_id', name='uq_event_scene_id'),
        Index('idx_events_scene_id', 'scene_id'),
        Index('idx_events_verb', 'verb'),
    )

class Spatial(Base):
    """공간 관계 테이블"""
    __tablename__ = 'spatial'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey('scenes.id', ondelete='CASCADE'), nullable=False)
    spatial_id = Column(String(100), nullable=False)
    subject_id = Column(String(100), nullable=False)
    predicate = Column(String(100), nullable=False)
    object_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 관계 설정
    scene = relationship("Scene", back_populates="spatial_relations")
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('scene_id', 'spatial_id', name='uq_spatial_scene_id'),
        Index('idx_spatial_scene_id', 'scene_id'),
        Index('idx_spatial_predicate', 'predicate'),
    )

class Temporal(Base):
    """시간 관계 테이블"""
    __tablename__ = 'temporal'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey('scenes.id', ondelete='CASCADE'), nullable=False)
    temporal_id = Column(String(100), nullable=False)
    subject_id = Column(String(100), nullable=False)
    predicate = Column(String(100), nullable=False)
    object_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 관계 설정
    scene = relationship("Scene", back_populates="temporal_relations")
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('scene_id', 'temporal_id', name='uq_temporal_scene_id'),
        Index('idx_temporal_scene_id', 'scene_id'),
        Index('idx_temporal_predicate', 'predicate'),
    )

class Embedding(Base):
    """임베딩 벡터 테이블"""
    __tablename__ = 'embeddings'
    
    node_id = Column(String(100), primary_key=True)  # node_id를 기본키로 사용
    node_type = Column(String(50), nullable=False)
    # pgvector의 Vector 타입 사용 (384차원)
    embedding = Column(Vector(384))
    created_at = Column(DateTime, default=func.now())
    
    # 제약 조건
    __table_args__ = (
        Index('idx_embeddings_node_type', 'node_type'),
    )

# 데이터베이스 연결 설정
def get_database_url() -> str:
    """데이터베이스 URL 생성"""
    return (
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:"
        f"{os.getenv('DB_PASSWORD', 'password')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'scene_graph_db')}"
    )

def create_engine_instance():
    """SQLAlchemy 엔진 생성"""
    database_url = get_database_url()
    return create_engine(
        database_url,
        echo=False,  # SQL 쿼리 로깅 (개발 시 True로 설정)
        pool_pre_ping=True,  # 연결 상태 확인
        pool_recycle=3600,  # 1시간마다 연결 재생성
    )

def create_session_factory(engine):
    """세션 팩토리 생성"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 전역 엔진 및 세션 팩토리
engine = create_engine_instance()
SessionLocal = create_session_factory(engine)

def get_db_session():
    """데이터베이스 세션 생성 (의존성 주입용)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """모든 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("✅ SQLAlchemy 테이블 생성 완료")

def drop_tables():
    """모든 테이블 삭제 (개발/테스트용)"""
    Base.metadata.drop_all(bind=engine)
    print("✅ SQLAlchemy 테이블 삭제 완료")
