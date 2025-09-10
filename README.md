# Scene Graph Database API Server

미디어 장면 그래프 데이터베이스를 위한 REST API 서버입니다. 비디오 정보, 장면, 노드 정보 및 임베딩 정보를 저장하고 관리합니다.

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   API Server    │    │   PostgreSQL    │
│   (Docker)      │◄──►│   (FastAPI)     │◄──►│   + pgvector    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**🔒 보안 정책**: 클라이언트는 API를 통해서만 데이터베이스에 접근할 수 있으며, 직접적인 데이터베이스 연결은 보안상 허용되지 않습니다.

## ✨ 주요 기능

- **장면그래프 저장**: 비디오, 장면, 객체, 이벤트, 공간관계, 시간관계 노드 저장
- **임베딩 관리**: 384차원 벡터 임베딩 저장 및 검색 (pgvector)
- **REST API**: FastAPI 기반 완전한 REST API 제공
- **ORM 기반**: SQLAlchemy ORM으로 타입 안전한 데이터베이스 접근
- **Docker 지원**: 모든 서비스가 Docker 컨테이너로 구성
- **마이그레이션**: Alembic을 통한 데이터베이스 스키마 관리

## 🚀 빠른 시작

### 1. Docker로 실행 (권장)

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api_server
```

### 2. 클라이언트 테스트

```bash
# 클라이언트 컨테이너 접속
docker exec -it scene_graph_client_test bash

# 장면그래프 데이터 업로드 테스트
python scene_graph_api_uploader.py

# API 테스트
python test_new_apis.py

# 저장된 데이터 확인
python check_stored_data.py
```

### 3. 로컬 개발 환경

```bash
# 환경 변수 설정
cp env.example .env

# PostgreSQL만 Docker로 실행
docker-compose up postgres -d

# 서버 의존성 설치
cd server && pip install -r requirements.txt

# 데이터베이스 마이그레이션
cd server && alembic upgrade head

# API 서버 실행
cd server && python start_server.py
```

## 📊 데이터베이스 스키마

### 핵심 테이블
- **VIDEO**: 드라마 및 에피소드 정보
- **SCENES**: 장면 메타데이터 (장소, 시간, 분위기, 프레임 범위)
- **OBJECTS**: 객체 노드 (인물, 물체 등)
- **EVENTS**: 이벤트 노드 (행동, 동작)
- **SPATIAL**: 공간 관계 (위치, 방향 등)
- **TEMPORAL**: 시간 관계 (순서, 동시성 등)
- **EMBEDDINGS**: 벡터 임베딩 (384차원, pgvector)

### 관계 구조
```
VIDEO (1) ──→ (N) SCENES (1) ──→ (N) OBJECTS
                    │
                    ├──→ (N) EVENTS
                    ├──→ (N) SPATIAL
                    └──→ (N) TEMPORAL

EMBEDDINGS ──→ (참조) OBJECTS/EVENTS/SPATIAL/TEMPORAL
```

## 🗂️ 프로젝트 구조

```
media-graph-db/
├── server/                    # API 서버
│   ├── app/
│   │   └── main.py          # FastAPI 메인 애플리케이션
│   ├── models/
│   │   ├── orm_models.py    # SQLAlchemy ORM 모델
│   │   └── api_schemas.py   # Pydantic API 스키마
│   ├── database/
│   │   └── database_manager.py # 데이터베이스 관리 클래스
│   ├── alembic/             # 데이터베이스 마이그레이션
│   │   └── versions/        # 마이그레이션 파일들
│   ├── requirements.txt     # 서버 의존성
│   ├── Dockerfile          # 서버 Docker 이미지
│   └── start_server.py     # 서버 시작 스크립트
├── client/                   # 클라이언트 테스트 코드
│   ├── scene_graph_api_uploader.py # 데이터 업로드 클라이언트
│   ├── test_new_apis.py     # API 테스트 클라이언트
│   ├── check_stored_data.py # 저장된 데이터 확인 클라이언트
│   ├── data/               # 테스트 데이터
│   │   ├── *.json         # 장면그래프 JSON 파일
│   │   └── *.pt           # 임베딩 PT 파일
│   ├── requirements.txt   # 클라이언트 의존성
│   └── Dockerfile        # 클라이언트 Docker 이미지
├── docker-compose.yml      # Docker 서비스 설정
├── init.sql               # PostgreSQL 초기화 스크립트
└── README.md             # 프로젝트 문서
```

## 🔌 API 엔드포인트

### 기본 정보
- `GET /` - 서버 상태 확인
- `GET /health` - 헬스 체크

### 비디오 관리
- `POST /videos` - 비디오 생성
- `GET /videos` - 비디오 목록 조회
- `GET /videos/{video_unique_id}` - 비디오 상세 정보 및 장면 목록

### 장면 관리
- `POST /scenes` - 장면 데이터 생성 (임베딩 포함)
- `GET /scenes/{scene_id}` - 장면 그래프 전체 조회
- `GET /scenes/{scene_id}/objects` - 장면의 객체 노드들
- `GET /scenes/{scene_id}/events` - 장면의 이벤트 노드들
- `GET /scenes/{scene_id}/spatial` - 장면의 공간관계들
- `GET /scenes/{scene_id}/temporal` - 장면의 시간관계들
- `GET /scenes/{scene_id}/embeddings` - 장면의 임베딩 정보들

### 노드 관리
- `POST /objects` - 객체 노드 생성
- `POST /events` - 이벤트 노드 생성
- `POST /spatial` - 공간관계 생성
- `POST /temporal` - 시간관계 생성

### 검색
- `POST /search/vector` - 벡터 기반 유사도 검색
- `POST /search/hybrid` - 하이브리드 검색 (텍스트 + 벡터)

## 🛠️ 개발 환경

### 요구사항
- Python 3.11+
- PostgreSQL 15+
- pgvector 확장
- Docker & Docker Compose

### 주요 패키지
- **FastAPI**: 웹 프레임워크
- **SQLAlchemy**: ORM
- **Alembic**: 데이터베이스 마이그레이션
- **pgvector**: 벡터 검색 확장
- **psycopg2**: PostgreSQL 드라이버
- **uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증

## 🔄 데이터베이스 마이그레이션

### 마이그레이션 실행
```bash
cd server
alembic upgrade head
```

### 새 마이그레이션 생성
```bash
cd server
alembic revision --autogenerate -m "설명"
```

### 마이그레이션 롤백
```bash
cd server
alembic downgrade -1
```

## 📈 성능 최적화

### 데이터베이스
- 적절한 인덱스 설정 (이미 구현됨)
- pgvector 인덱스 최적화
- 연결 풀 설정

### API 서버
- 비동기 처리
- 응답 캐싱 (필요시)
- 로드 밸런싱 (대용량 트래픽)

## 🐛 문제 해결

### 일반적인 문제
1. **DB 연결 실패**: PostgreSQL 서비스 상태 확인
2. **pgvector 오류**: 확장 설치 확인
3. **포트 충돌**: 8000, 5432 포트 사용 여부 확인

### 로그 확인
```bash
# API 서버 로그
docker-compose logs api_server

# PostgreSQL 로그
docker-compose logs postgres

# 클라이언트 로그
docker-compose logs client_test
```

### 컨테이너 재시작
```bash
# 특정 서비스 재시작
docker-compose restart api_server

# 모든 서비스 재시작
docker-compose restart
```

## 🔒 보안 고려사항

### 프로덕션 환경
1. **환경 변수**: 민감한 정보는 환경 변수로 관리
2. **네트워크**: DB 서버를 내부 네트워크에 배치
3. **인증**: 강력한 비밀번호 및 SSL 연결
4. **방화벽**: 특정 IP에서만 접근 허용

### 권장 설정
```bash
# .env 파일에서
DB_PASSWORD=강력한_비밀번호_사용
SECRET_KEY=랜덤_시크릿_키_생성
ALLOWED_HOSTS=실제_도메인_명시
```

## 📚 사용 예시

### 1. 장면그래프 데이터 업로드
```python
from client.scene_graph_api_uploader import SceneGraphAPIUploader

uploader = SceneGraphAPIUploader("http://localhost:8000")
success = uploader.upload_scene_graph("data/scene_data.json")
```

### 2. API를 통한 데이터 조회
```python
import requests

# 비디오 목록 조회
response = requests.get("http://localhost:8000/videos")
videos = response.json()

# 특정 장면의 그래프 조회
response = requests.get("http://localhost:8000/scenes/1")
scene_graph = response.json()
```

### 3. 벡터 검색
```python
# 벡터 검색 요청
search_data = {
    "query_embedding": [0.1, 0.2, ...],  # 384차원 벡터
    "node_type": "object",
    "top_k": 5
}
response = requests.post("http://localhost:8000/search/vector", json=search_data)
results = response.json()
```

## 📚 추가 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/)
- [Alembic 마이그레이션 가이드](https://alembic.sqlalchemy.org/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [pgvector 문서](https://github.com/pgvector/pgvector)

## 🤝 기여

버그 리포트 및 기능 제안은 이슈로 등록해 주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.