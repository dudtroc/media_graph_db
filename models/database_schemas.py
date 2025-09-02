"""
데이터베이스 스키마 정의 및 SQL 스크립트
"""

# 테이블 생성 SQL 스크립트
CREATE_TABLES_SQL = """
-- 1. VIDEO 테이블 (드라마 + 에피소드 통합)
CREATE TABLE IF NOT EXISTS video (
    id SERIAL PRIMARY KEY,
    video_unique_id INTEGER NOT NULL UNIQUE,
    drama_name VARCHAR(255) NOT NULL,
    episode_number VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(drama_name, episode_number)
);

-- 2. SCENES 테이블 (장면)
CREATE TABLE IF NOT EXISTS scenes (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES video(id) ON DELETE CASCADE,
    scene_number VARCHAR(255) NOT NULL,
    scene_place TEXT,
    scene_time VARCHAR(100),
    scene_atmosphere TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id, scene_number)
);

-- 3. OBJECTS 테이블 (객체 노드)
CREATE TABLE IF NOT EXISTS objects (
    id SERIAL PRIMARY KEY,
    scene_id INTEGER REFERENCES scenes(id) ON DELETE CASCADE,
    object_id INTEGER NOT NULL,
    super_type VARCHAR(100) NOT NULL,
    type_of VARCHAR(100) NOT NULL,
    label TEXT NOT NULL,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(scene_id, object_id)
);

-- 4. EVENTS 테이블 (이벤트 노드)
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    scene_id INTEGER REFERENCES scenes(id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    verb VARCHAR(100) NOT NULL,
    object_id INTEGER,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(scene_id, event_id)
);

-- 5. SPATIAL 테이블 (공간 관계)
CREATE TABLE IF NOT EXISTS spatial (
    id SERIAL PRIMARY KEY,
    scene_id INTEGER REFERENCES scenes(id) ON DELETE CASCADE,
    spatial_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    predicate VARCHAR(100) NOT NULL,
    object_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(scene_id, spatial_id)
);

-- 6. TEMPORAL 테이블 (시간 관계)
CREATE TABLE IF NOT EXISTS temporal (
    id SERIAL PRIMARY KEY,
    scene_id INTEGER REFERENCES scenes(id) ON DELETE CASCADE,
    temporal_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    predicate VARCHAR(100) NOT NULL,
    object_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(scene_id, temporal_id)
);

-- 7. EMBEDDINGS 테이블 (임베딩 벡터)
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    node_id INTEGER NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(node_id, node_type)
);
"""

# 인덱스 생성 SQL 스크립트
CREATE_INDEXES_SQL = """
-- 기본 인덱스
CREATE INDEX IF NOT EXISTS idx_video_unique_id ON video(video_unique_id);
CREATE INDEX IF NOT EXISTS idx_video_drama_episode ON video(drama_name, episode_number);
CREATE INDEX IF NOT EXISTS idx_scenes_video_id ON scenes(video_id);
CREATE INDEX IF NOT EXISTS idx_objects_scene_id ON objects(scene_id);
CREATE INDEX IF NOT EXISTS idx_events_scene_id ON events(scene_id);
CREATE INDEX IF NOT EXISTS idx_spatial_scene_id ON spatial(scene_id);
CREATE INDEX IF NOT EXISTS idx_temporal_scene_id ON temporal(scene_id);

-- 검색용 인덱스
CREATE INDEX IF NOT EXISTS idx_objects_super_type ON objects(super_type);
CREATE INDEX IF NOT EXISTS idx_objects_type_of ON objects(type_of);
CREATE INDEX IF NOT EXISTS idx_objects_label ON objects(label);
CREATE INDEX IF NOT EXISTS idx_events_verb ON events(verb);
CREATE INDEX IF NOT EXISTS idx_spatial_predicate ON spatial(predicate);
CREATE INDEX IF NOT EXISTS idx_temporal_predicate ON temporal(predicate);
"""

# pgvector 인덱스 생성 SQL 스크립트
CREATE_VECTOR_INDEXES_SQL = """
-- 벡터 검색 인덱스 (pgvector 확장 필요)
CREATE INDEX IF NOT EXISTS idx_embeddings_object ON embeddings USING ivfflat (embedding vector_cosine_ops) WHERE node_type = 'object';
CREATE INDEX IF NOT EXISTS idx_embeddings_event ON embeddings USING ivfflat (embedding vector_cosine_ops) WHERE node_type = 'event';
CREATE INDEX IF NOT EXISTS idx_embeddings_spatial ON embeddings USING ivfflat (embedding vector_cosine_ops) WHERE node_type = 'spatial';
CREATE INDEX IF NOT EXISTS idx_embeddings_temporal ON embeddings USING ivfflat (embedding vector_cosine_ops) WHERE node_type = 'temporal';
"""

# 외래키 제약 조건 SQL 스크립트
ADD_FOREIGN_KEYS_SQL = """
-- 외래키 제약 조건 추가
ALTER TABLE scenes ADD CONSTRAINT IF NOT EXISTS fk_scenes_video 
    FOREIGN KEY (video_id) REFERENCES video(id) ON DELETE CASCADE;

ALTER TABLE objects ADD CONSTRAINT IF NOT EXISTS fk_objects_scene 
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE;

ALTER TABLE events ADD CONSTRAINT IF NOT EXISTS fk_events_scene 
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE;

ALTER TABLE spatial ADD CONSTRAINT IF NOT EXISTS fk_spatial_scene 
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE;

ALTER TABLE temporal ADD CONSTRAINT IF NOT EXISTS fk_temporal_scene 
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE;
"""

