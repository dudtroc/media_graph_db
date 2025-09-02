-- PostgreSQL 초기화 스크립트
-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 데이터베이스 생성 확인
SELECT 'pgvector extension activated successfully' as status;

