# API 통신 방식으로 마이그레이션 완료

## 🔄 **문제점과 해결방안**

### ❌ **기존 문제점**
현재 클라이언트 코드가 서버 코드를 직접 import하여 사용하는 문제가 있었습니다:

```python
# 문제가 있던 코드 (client/scene_graph_uploader.py)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))
from database.database_manager import SceneGraphDatabaseManager

class SceneGraphUploader:
    def __init__(self):
        self.db_manager = SceneGraphDatabaseManager()  # 직접 DB 접근
```

### ✅ **해결방안**
참고 프로젝트(`/home/ktva/PROJECT/MEDIA/media-insight`)의 구조를 분석하여 API 통신 방식으로 수정했습니다.

## 🏗️ **새로운 아키텍처**

### **서버 측 (API)**
```
server/
├── app/
│   ├── main.py              # FastAPI 애플리케이션
│   └── __init__.py
├── start_server.py          # 서버 시작 스크립트
├── database/
│   └── database_manager.py  # DB 매니저 (서버 내부용)
└── models/
    ├── orm_models.py        # ORM 모델
    └── api_schemas.py       # API 스키마
```

### **클라이언트 측 (API 통신)**
```
client/
├── scene_graph_api_uploader.py  # API를 통한 업로더
├── run_api_uploader.py          # API 업로더 실행
├── test_api_communication.py    # API 통신 테스트
└── start_client.py              # API 통신 방식으로 수정
```

## 🚀 **구현된 API 엔드포인트**

### **기본 엔드포인트**
- `GET /` - 루트 엔드포인트
- `GET /health` - 헬스 체크

### **비디오 관련**
- `POST /videos` - 비디오 생성
- `GET /videos` - 비디오 목록 조회
- `GET /videos/{video_unique_id}/summary` - 비디오 요약

### **장면 관련**
- `POST /scenes` - 장면 데이터 생성 (임베딩 포함)
- `GET /scenes/{scene_id}` - 장면 그래프 조회

### **노드 관련**
- `POST /objects` - 객체 노드 생성
- `POST /events` - 이벤트 노드 생성
- `POST /spatial` - 공간 관계 생성
- `POST /temporal` - 시간 관계 생성

### **검색 관련**
- `POST /search/vector` - 벡터 기반 유사도 검색
- `POST /search/hybrid` - 하이브리드 검색

## 📝 **사용 방법**

### **1. 서버 시작**
```bash
cd server
pip install -r requirements.txt
python start_server.py
```

### **2. 클라이언트 테스트**
```bash
cd client
pip install -r requirements.txt
python start_client.py
```

### **3. API 통신 테스트**
```bash
cd client
python test_api_communication.py
```

### **4. 장면그래프 업로드**
```bash
cd client
python run_api_uploader.py
```

## 🔧 **주요 변경사항**

### **1. 서버 측**
- **FastAPI 애플리케이션 생성**: `server/app/main.py`
- **API 엔드포인트 구현**: 모든 CRUD 작업을 REST API로 제공
- **벡터 검색 지원**: pgvector를 사용한 벡터 검색 API
- **의존성 주입**: 데이터베이스 매니저를 의존성으로 주입

### **2. 클라이언트 측**
- **API 클라이언트 생성**: `SceneGraphAPIUploader` 클래스
- **HTTP 통신**: `requests` 라이브러리를 사용한 API 호출
- **에러 처리**: API 응답 상태 코드 및 오류 메시지 처리
- **헬스 체크**: 서버 연결 상태 확인

### **3. 데이터 흐름**
```
클라이언트 → HTTP API → FastAPI 서버 → SQLAlchemy ORM → PostgreSQL + pgvector
```

## 🧪 **테스트 결과**

### **API 통신 테스트**
- ✅ 헬스 체크
- ✅ 비디오 생성
- ✅ 장면 생성 (임베딩 포함)
- ✅ 노드 생성 (객체, 이벤트, 공간, 시간)
- ✅ 벡터 검색
- ✅ 데이터 조회

### **장면그래프 업로드 테스트**
- ✅ JSON 파일 파싱
- ✅ PT 파일 로드 (임베딩 데이터)
- ✅ API를 통한 비디오 생성
- ✅ API를 통한 장면 생성
- ✅ API를 통한 노드 데이터 저장

## 🔒 **보안 및 아키텍처 개선**

### **장점**
1. **관심사 분리**: 클라이언트와 서버가 명확히 분리됨
2. **확장성**: API를 통해 다양한 클라이언트 지원 가능
3. **보안**: 직접 DB 접근 차단, API 레벨에서 검증
4. **유지보수성**: 서버 로직 변경 시 클라이언트 영향 최소화
5. **표준화**: REST API 표준 준수

### **참고 프로젝트 구조 적용**
참고 프로젝트(`media-insight`)의 구조를 분석하여:
- **FastAPI 기반 API 서버** 구조 적용
- **클라이언트-서버 분리** 아키텍처 적용
- **의존성 주입** 패턴 적용
- **에러 처리** 및 **헬스 체크** 구현

## 📊 **성능 및 기능**

### **벡터 저장**
- ✅ pgvector를 사용한 실제 벡터 형태 저장
- ✅ 384차원 임베딩 벡터 지원
- ✅ 코사인 유사도 검색 지원

### **API 성능**
- ✅ 비동기 처리 지원 (FastAPI)
- ✅ CORS 설정으로 웹 클라이언트 지원
- ✅ 자동 API 문서 생성 (`/docs`)

## 🎯 **결론**

**클라이언트가 서버 코드를 직접 사용하는 문제를 완전히 해결**하고, **API 통신을 통한 깔끔한 아키텍처**로 마이그레이션했습니다.

이제 클라이언트는 HTTP API를 통해 데이터베이스에 접근하며, 장면그래프와 임베딩 정보를 정상적으로 저장할 수 있습니다. 참고 프로젝트의 구조를 적용하여 확장 가능하고 유지보수하기 쉬운 시스템이 되었습니다.
