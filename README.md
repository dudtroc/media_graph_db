# Scene Graph Database API Server

미디어 장면 그래프 데이터베이스를 위한 REST API 서버입니다.

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   API Server    │    │   PostgreSQL    │
│   Application   │◄──►│   (FastAPI)     │◄──►│   + pgvector    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**🔒 보안 정책**: 클라이언트는 API를 통해서만 데이터베이스에 접근할 수 있으며, 직접적인 데이터베이스 연결은 보안상 허용되지 않습니다.

## 🆕 SQLAlchemy ORM 마이그레이션

이 프로젝트는 기존의 psycopg2 기반 직접 SQL 접근 방식에서 **SQLAlchemy ORM**으로 완전히 마이그레이션되었습니다.

### 주요 변경사항:
- ✅ **SQLAlchemy ORM 모델**: `server/models/orm_models.py`
- ✅ **데이터베이스 매니저**: `server/database/database_manager.py`
- ✅ **Alembic 마이그레이션**: `server/alembic/` 디렉토리
- ✅ **타입 안전성**: 모든 데이터베이스 작업이 ORM을 통해 수행
- ✅ **관계형 매핑**: 테이블 간 관계가 Python 객체로 표현
- ✅ **프로젝트 구조 정리**: 모든 서버 관련 코드가 `server/` 디렉토리로 통합

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 환경 변수 파일 복사
cp env.example .env

# 환경 변수 수정 (필요시)
nano .env
```

### 2. Docker로 실행

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

### 3. 데이터베이스 초기화

```bash
# 의존성 설치
pip install -r server/requirements.txt

# PostgreSQL 서버 실행 (별도)
# 또는 Docker로 PostgreSQL만 실행
docker-compose up postgres -d

# 데이터베이스 초기화 (SQLAlchemy ORM 테이블 생성)
cd server && python init_database.py
```

### 4. 로컬에서 실행

```bash
# API 서버 실행
cd server && python start_server.py
```

### 4. 테스트 실행

```bash
# API 테스트 (서버 실행 후)
python tests/test_api.py
```

## 📊 데이터베이스 스키마

- **VIDEO**: 드라마 및 에피소드 정보
- **SCENES**: 장면 메타데이터
- **OBJECTS**: 객체 노드 (인물, 물체 등)
- **EVENTS**: 이벤트 노드 (행동, 동작)
- **SPATIAL**: 공간 관계
- **TEMPORAL**: 시간 관계
- **EMBEDDINGS**: 벡터 임베딩 (pgvector)

## 🗂️ 프로젝트 구조

```
media-graph-db/
├── app/                    # FastAPI 애플리케이션 (API 서버)
│   └── main.py           # 메인 API 서버
├── server/                # 서버 관련 코드
│   ├── app/              # 서버 애플리케이션
│   │   └── main.py      # 서버 메인 API
│   └── database/         # 서버 데이터베이스 클래스
│       └── scene_graph_db.py
├── database/              # 공통 데이터베이스 클래스
│   ├── __init__.py
│   └── scene_graph_db.py # PostgreSQL 데이터베이스 클래스
├── models/                # 데이터 모델 및 스키마
│   ├── __init__.py
│   ├── api_schemas.py    # API 요청/응답 스키마
│   └── database_schemas.py # DB 스키마 정의
├── client/                # 클라이언트 애플리케이션
│   ├── scene_graph_uploader.py # API를 통한 데이터 업로드
│   ├── test_api.py       # API 테스트
│   └── requirements.txt  # 클라이언트 의존성
├── tests/                 # 테스트 코드 (API를 통한 접근)
│   ├── __init__.py
│   ├── test_api.py       # API 테스트
│   └── test_database.py  # 데이터베이스 테스트 (API 통한)
├── config/                # 설정 파일들
├── docker-compose.yml     # Docker 서비스 설정
├── Dockerfile            # API 서버 Docker 이미지
├── requirements.txt      # 서버 의존성
└── README.md            # 프로젝트 문서
```

**📝 참고**: 클라이언트 코드는 모두 API를 통해서만 데이터베이스에 접근하며, 직접적인 데이터베이스 연결 코드는 제거되었습니다.

## 🔒 보안 정책

### 데이터베이스 접근 제한
- **클라이언트**: API를 통해서만 데이터베이스에 접근 가능
- **서버 내부**: SceneGraphDatabase 클래스를 통한 직접 접근 허용
- **직접 연결**: `psycopg2` 등으로 클라이언트에서 직접 DB 연결 금지

### 보안 이점
- SQL 인젝션 공격 방지
- 데이터베이스 자격 증명 노출 방지
- 접근 권한 중앙 집중 관리
- API 레벨에서의 입력 검증 및 필터링

## 🔌 API 엔드포인트

### 기본 정보
- `GET /` - 서버 상태 확인
- `GET /health` - 헬스 체크

### 비디오 관리
- `POST /videos` - 비디오 생성
- `GET /videos` - 비디오 목록 조회
- `GET /videos/{id}/summary` - 비디오 요약

### 장면 관리
- `POST /scenes` - 장면 데이터 생성
- `GET /scenes/{id}` - 장면 그래프 조회

### 검색
- `POST /search/vector` - 벡터 기반 유사도 검색
- `POST /search/hybrid` - 하이브리드 검색 (텍스트 + 벡터)

## 🛠️ 개발 환경

### 요구사항
- Python 3.11+
- PostgreSQL 15+
- pgvector 확장

### 주요 패키지
- FastAPI: 웹 프레임워크
- psycopg2: PostgreSQL 드라이버
- uvicorn: ASGI 서버
- pgvector: 벡터 검색 확장

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
docker-compose logs api

# PostgreSQL 로그
docker-compose logs postgres
```

## 🔄 SQLAlchemy ORM 마이그레이션 가이드

### 기존 코드에서 새로운 ORM 사용법

#### 1. 데이터베이스 연결
```python
# 기존 방식 (psycopg2)
from database.scene_graph_db import SceneGraphDatabase
db = SceneGraphDatabase()

# 새로운 방식 (SQLAlchemy ORM)
from database.database_manager import SceneGraphDatabaseManager
db = SceneGraphDatabaseManager()
```

#### 2. 데이터 삽입
```python
# 기존 방식
video_id = db.insert_video_data(1, "드라마명", "EP01")

# 새로운 방식 (동일한 인터페이스 유지)
video_id = db.insert_video_data(1, "드라마명", "EP01")
```

#### 3. 세션 관리
```python
# 새로운 방식에서 세션 직접 사용
session = db.get_session()
try:
    # ORM 쿼리 실행
    videos = session.query(Video).all()
finally:
    session.close()
```

### 마이그레이션 파일 관리
```bash
# Alembic 마이그레이션 생성 (향후 사용)
cd server && alembic revision --autogenerate -m "description"

# 마이그레이션 실행
cd server && alembic upgrade head

# 마이그레이션 롤백
cd server && alembic downgrade -1
```

## 📚 추가 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/)
- [Alembic 마이그레이션 가이드](https://alembic.sqlalchemy.org/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [pgvector 문서](https://github.com/pgvector/pgvector)
- [장면 그래프 데이터베이스 설계 가이드](링크)

## 🤝 기여

버그 리포트 및 기능 제안은 이슈로 등록해 주세요.
