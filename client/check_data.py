#!/usr/bin/env python3
"""
데이터베이스 직접 접근을 통한 데이터 확인 도구
"""

import subprocess
import json

def run_db_query(query):
    """데이터베이스 쿼리 실행"""
    cmd = [
        "docker", "exec", "-i", "scene_graph_postgres",
        "psql", "-U", "postgres", "-d", "scene_graph_db", "-t", "-c", query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Exception: {e}"

def check_all_data():
    """모든 데이터 확인"""
    print("🔍 장면그래프 및 임베딩 데이터 저장 상태 확인")
    print("=" * 60)
    
    # 1. 기본 통계
    print("\n📊 데이터베이스 통계")
    print("-" * 30)
    
    queries = {
        "비디오": "SELECT COUNT(*) FROM video",
        "장면": "SELECT COUNT(*) FROM scenes", 
        "객체": "SELECT COUNT(*) FROM objects",
        "이벤트": "SELECT COUNT(*) FROM events",
        "공간관계": "SELECT COUNT(*) FROM spatial",
        "시간관계": "SELECT COUNT(*) FROM temporal",
        "임베딩": "SELECT COUNT(*) FROM embeddings"
    }
    
    for name, query in queries.items():
        result = run_db_query(query)
        if result.isdigit():
            print(f"✅ {name}: {result}개")
        else:
            print(f"❌ {name}: {result}")
    
    # 2. 비디오 상세 정보
    print("\n📺 비디오 상세 정보")
    print("-" * 30)
    
    video_query = """
    SELECT id, title, episode, created_at 
    FROM video 
    ORDER BY id;
    """
    
    result = run_db_query(video_query)
    if result and not result.startswith("Error") and not result.startswith("Exception"):
        lines = result.split('\n')
        for line in lines:
            if line.strip():
                parts = line.strip().split('|')
                if len(parts) >= 4:
                    print(f"  - ID: {parts[0].strip()}, 제목: {parts[1].strip()}, 에피소드: {parts[2].strip()}")
    
    # 3. 장면 상세 정보
    print("\n🎭 장면 상세 정보")
    print("-" * 30)
    
    scene_query = """
    SELECT s.id, s.scene_number, s.scene_place, s.start_frame, s.end_frame, v.title
    FROM scenes s
    JOIN video v ON s.video_id = v.id
    ORDER BY s.id;
    """
    
    result = run_db_query(scene_query)
    if result and not result.startswith("Error") and not result.startswith("Exception"):
        lines = result.split('\n')
        for line in lines:
            if line.strip():
                parts = line.strip().split('|')
                if len(parts) >= 6:
                    print(f"  - 장면 {parts[1].strip()}: {parts[2].strip()} ({parts[3].strip()}-{parts[4].strip()}) - {parts[5].strip()}")
    
    # 4. 임베딩 상세 정보
    print("\n🔗 임베딩 상세 정보")
    print("-" * 30)
    
    embedding_query = """
    SELECT 
        node_type,
        COUNT(*) as count,
        vector_dims(embedding) as embedding_dim
    FROM embeddings 
    GROUP BY node_type, vector_dims(embedding)
    ORDER BY node_type;
    """
    
    result = run_db_query(embedding_query)
    if result and not result.startswith("Error") and not result.startswith("Exception"):
        lines = result.split('\n')
        total_embeddings = 0
        for line in lines:
            if line.strip():
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    node_type = parts[0].strip()
                    count = int(parts[1].strip())
                    dim = parts[2].strip()
                    total_embeddings += count
                    print(f"  {node_type}: {count}개 (차원: {dim})")
        print(f"✅ 총 임베딩 수: {total_embeddings}개")
    
    # 5. 노드 타입별 상세 정보
    print("\n🔍 노드 타입별 상세 정보")
    print("-" * 30)
    
    # 객체 정보
    object_query = """
    SELECT type_of, COUNT(*) as count
    FROM objects
    GROUP BY type_of
    ORDER BY count DESC;
    """
    
    result = run_db_query(object_query)
    if result and not result.startswith("Error") and not result.startswith("Exception"):
        print("👥 객체 타입별 분포:")
        lines = result.split('\n')
        for line in lines:
            if line.strip():
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    print(f"  - {parts[0].strip()}: {parts[1].strip()}개")
    
    # 이벤트 정보
    event_query = """
    SELECT verb, COUNT(*) as count
    FROM events
    GROUP BY verb
    ORDER BY count DESC;
    """
    
    result = run_db_query(event_query)
    if result and not result.startswith("Error") and not result.startswith("Exception"):
        print("🎬 이벤트 동사별 분포:")
        lines = result.split('\n')
        for line in lines:
            if line.strip():
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    print(f"  - {parts[0].strip()}: {parts[1].strip()}개")
    
    # 6. 임베딩 샘플 확인
    print("\n📊 임베딩 샘플 (처음 5차원)")
    print("-" * 30)
    
    sample_query = """
    SELECT node_id, node_type, 
           array_to_string(embedding[1:5], ',') as sample_embedding
    FROM embeddings 
    ORDER BY node_type, node_id
    LIMIT 5;
    """
    
    result = run_db_query(sample_query)
    if result and not result.startswith("Error") and not result.startswith("Exception"):
        lines = result.split('\n')
        for line in lines:
            if line.strip():
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    node_id = parts[0].strip()
                    node_type = parts[1].strip()
                    sample = parts[2].strip()
                    print(f"  {node_type} {node_id}: [{sample}]")
    
    print("\n" + "=" * 60)
    print("✅ 데이터 확인 완료!")

def main():
    """메인 함수"""
    print("🚀 데이터베이스 직접 접근 데이터 확인 도구")
    print("=" * 60)
    
    try:
        check_all_data()
    except Exception as e:
        print(f"❌ 데이터 확인 실패: {e}")

if __name__ == "__main__":
    main()
