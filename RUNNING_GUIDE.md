# 🚀 Scene Graph Database 실행 가이드

## 📁 **새로운 프로젝트 구조**

```
media-graph-db/
├── server/                 # 🖥️ 서버 코드
│   ├── app/               # FastAPI 애플리케이션
│   ├── database/          # DB 구현 코드
│   ├── models/            # DB 스키마
│   ├── config/            # 서버 설정
│   ├── Dockerfile         # 서버 Docker 이미지
│   ├── requirements.txt   # 서버 의존성
│   └── start_server.py    # 서버 실행 스크립트
├── client/                 # 🧪 클라이언트 테스트 코드
│   ├── test_api.py        # API 테스트
│   ├── test_database.py   # DB 직접 테스트
│   ├── run_tests.py       # 테스트 실행기
│   ├── requirements.txt   # 클라이언트 의존성
│   └── start_client.py    # 클라이언트 실행 스크립트
├── docker-compose.yml      # 전체 서비스 설정
└── README.md              # 프로젝트 문서
```

## 🖥️ **서버 실행 방법**

### 1. Docker로 전체 서비스 실행 (권장)
```bash
# 모든 서비스 시작 (PostgreSQL + PostgREST + FastAPI)
docker-compose up -d

# 로그 확인
docker-compose logs -f api_server
```

### 2. 로컬에서 서버만 실행
```bash
# 서버 디렉토리로 이동
cd server

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp ../env.example .env
# .env 파일 수정 (DB 연결 정보)

# 서버 실행
python start_server.py
```

### 3. 서버별 개별 실행
```bash
# PostgreSQL만 실행
docker-compose up postgres -d

# PostgREST만 실행 (자동 REST API)
docker-compose up postgrest -d

# FastAPI 서버만 실행
docker-compose up api_server -d
```

## 🧪 **클라이언트 테스트 방법**

### 1. Docker로 클라이언트 테스트
```bash
# 클라이언트 테스트 컨테이너 실행
docker-compose up client_test

# 또는 백그라운드 실행
docker-compose up -d client_test
docker-compose logs -f client_test
```

### 2. 로컬에서 클라이언트 테스트
```bash
# 클라이언트 디렉토리로 이동
cd client

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp ../env.example .env
# .env 파일 수정

# 클라이언트 테스트 실행
python start_client.py
```

### 3. 개별 테스트 실행
```bash
# API 테스트만 실행
python test_api.py

# 모든 테스트 실행
python run_tests.py
```

## 🌐 **접근 가능한 서비스들**

### 서비스별 포트 및 URL
- **PostgreSQL**: `localhost:5432` (직접 DB 연결)
- **PostgREST**: `http://localhost:3000` (자동 REST API)
- **FastAPI**: `http://localhost:8000` (커스텀 API)
- **클라이언트**: 컨테이너 내부에서 실행

### PostgREST 자동 API 예시
```bash
# 테이블별 자동 REST API
GET http://localhost:3000/video
GET http://localhost:3000/scenes
GET http://localhost:3000/objects

# 필터링
GET http://localhost:3000/scenes?video_id=eq.1

# 정렬
GET http://localhost:3000/video?order=drama_name.asc
```

### FastAPI 커스텀 API 예시
```bash
# 서버 상태 확인
GET http://localhost:8000/health

# 비디오 생성
POST http://localhost:8000/videos

# 벡터 검색
POST http://localhost:8000/search/vector
```

## 🔧 **개발 환경 설정**

### 환경 변수 (.env)
```bash
# 데이터베이스 설정
DB_HOST=localhost
DB_NAME=scene_graph_db
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432

# API 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True

# 클라이언트 설정
API_URL=http://localhost:8000
```

### 의존성 설치
```bash
# 서버 의존성
cd server
pip install -r requirements.txt

# 클라이언트 의존성
cd ../client
pip install -r requirements.txt
```

## 🚨 **문제 해결**

### 일반적인 문제들
1. **포트 충돌**: 5432, 3000, 8000 포트 사용 여부 확인
2. **DB 연결 실패**: PostgreSQL 서비스 상태 확인
3. **의존성 오류**: requirements.txt 버전 호환성 확인

### 로그 확인
```bash
# 전체 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs postgres
docker-compose logs api_server
docker-compose logs client_test
```

## 📚 **사용 예시**

### 1. 전체 시스템 테스트
```bash
# 1. 서비스 시작
docker-compose up -d

# 2. 서비스 상태 확인
docker-compose ps

# 3. 클라이언트 테스트 실행
docker-compose up client_test
```

### 2. 단계별 테스트
```bash
# 1. PostgreSQL만 시작
docker-compose up postgres -d

# 2. 클라이언트로 DB 직접 테스트
cd client
python test_database.py

# 3. FastAPI 서버 시작
cd ../server
python start_server.py

# 4. API 테스트
cd ../client
python test_api.py
```

이제 서버와 클라이언트 코드가 명확하게 분리되어 있어서 각각의 역할과 실행 방법을 쉽게 이해할 수 있습니다! 🎉
