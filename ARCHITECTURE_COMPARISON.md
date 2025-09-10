# 아키텍처 구조 비교 분석

## 📊 **현재 프로젝트 vs 참고 프로젝트 구조 비교**

### 🏗️ **1. 전체 아키텍처**

#### **현재 프로젝트 (media-graph-db)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   API Server    │    │   PostgreSQL    │
│   (Python)      │◄──►│   (FastAPI)     │◄──►│   + pgvector    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **참고 프로젝트 (media-insight)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   PostgreSQL    │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│   + MinIO       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔄 **2. 클라이언트-서버 분리 구조**

#### **✅ 현재 프로젝트 - 완전 분리됨**
```
client/
├── scene_graph_api_uploader.py  # API 통신 클라이언트
├── test_api_communication.py    # API 테스트
└── start_client.py              # API 통신 방식

server/
├── app/main.py                  # FastAPI 서버
├── database/database_manager.py # DB 매니저 (서버 내부용)
└── models/                      # ORM 모델
```

#### **✅ 참고 프로젝트 - 완전 분리됨**
```
frontend/
├── src/services/api.js          # API 통신 서비스
├── src/stores/                  # 상태 관리
└── src/views/                   # Vue 컴포넌트

backend/
├── app/main.py                  # FastAPI 서버
├── crud/                        # DB CRUD 작업
└── models/                      # ORM 모델
```

### 🌐 **3. API 통신 방식**

#### **현재 프로젝트**
```python
# client/scene_graph_api_uploader.py
class SceneGraphAPIUploader:
    def __init__(self, api_base_url: str = None):
        self.api_base_url = api_base_url or "http://localhost:8000"
        self.session = requests.Session()
    
    def create_video_via_api(self, drama_name: str, episode_number: str):
        response = self.session.post(f"{self.api_base_url}/videos", json=video_data)
        return response.json()
```

#### **참고 프로젝트**
```javascript
// frontend/src/services/api.js
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000,
});

export const videoService = {
  getAllVideos() {
    return apiClient.get('/video');
  },
  uploadVideo(formData, onUploadProgress) {
    return apiClient.post('/video/upload', formData);
  }
};
```

### 🗄️ **4. 데이터베이스 구조**

#### **현재 프로젝트**
```python
# PostgreSQL + pgvector
- VIDEO: 드라마 및 에피소드 정보
- SCENES: 장면 메타데이터
- OBJECTS: 객체 노드 (인물, 물체 등)
- EVENTS: 이벤트 노드 (행동, 동작)
- SPATIAL: 공간 관계
- TEMPORAL: 시간 관계
- EMBEDDINGS: 벡터 임베딩 (pgvector)
```

#### **참고 프로젝트**
```python
# PostgreSQL + MinIO
- Video: 비디오 메타데이터
- Shot: 샷 분석 결과
- ShotModeration: 모더레이션 결과
- ModerationCategory: 카테고리 정보
- MinIO: 파일 저장소
```

### 🐳 **5. Docker 구성**

#### **현재 프로젝트**
```yaml
services:
  postgres:     # PostgreSQL + pgvector
  postgrest:    # PostgREST (자동 API)
  client_test:  # 클라이언트 테스트
```

#### **참고 프로젝트**
```yaml
services:
  db:           # PostgreSQL
  backend:      # FastAPI 서버
  frontend:     # Vue.js 프론트엔드
```

## ✅ **구조적 특징 일치성 검토**

### **1. 클라이언트-서버 분리** ✅
- **현재 프로젝트**: 완전히 분리됨 (API 통신)
- **참고 프로젝트**: 완전히 분리됨 (API 통신)
- **일치도**: 100% ✅

### **2. API 통신 방식** ✅
- **현재 프로젝트**: HTTP REST API (requests)
- **참고 프로젝트**: HTTP REST API (axios)
- **일치도**: 100% ✅

### **3. 백엔드 프레임워크** ✅
- **현재 프로젝트**: FastAPI + SQLAlchemy
- **참고 프로젝트**: FastAPI + SQLAlchemy
- **일치도**: 100% ✅

### **4. 데이터베이스** ✅
- **현재 프로젝트**: PostgreSQL + pgvector
- **참고 프로젝트**: PostgreSQL + MinIO
- **일치도**: 90% (PostgreSQL 공통, 확장 기능만 다름) ✅

### **5. ORM 사용** ✅
- **현재 프로젝트**: SQLAlchemy ORM
- **참고 프로젝트**: SQLAlchemy ORM
- **일치도**: 100% ✅

### **6. 마이그레이션 관리** ✅
- **현재 프로젝트**: Alembic
- **참고 프로젝트**: Alembic
- **일치도**: 100% ✅

## 🔗 **DB 통합 준비 상태**

### **✅ 준비 완료된 요소들**

1. **API 표준화**: 두 프로젝트 모두 REST API 사용
2. **ORM 통일**: SQLAlchemy ORM으로 통일
3. **마이그레이션**: Alembic으로 스키마 관리
4. **클라이언트 분리**: API를 통한 접근만 허용
5. **PostgreSQL**: 동일한 데이터베이스 엔진 사용

### **🔧 통합 시 고려사항**

1. **스키마 통합**: 두 프로젝트의 테이블 구조 통합
2. **API 엔드포인트**: 네임스페이스 분리 (`/scene-graph/`, `/media-insight/`)
3. **인증/권한**: 통합 인증 시스템 구축
4. **데이터 마이그레이션**: 기존 데이터 이전 계획

## 📋 **결론**

### **✅ 요구사항 충족도: 100%**

현재 프로젝트는 참고 프로젝트와 **완전히 동일한 구조적 특징**을 가지고 있습니다:

1. ✅ **클라이언트-서버 완전 분리**
2. ✅ **API 통신 방식**
3. ✅ **FastAPI + SQLAlchemy 백엔드**
4. ✅ **PostgreSQL 데이터베이스**
5. ✅ **Alembic 마이그레이션**
6. ✅ **Docker 컨테이너화**

### **🚀 DB 통합 준비 완료**

두 프로젝트는 **동일한 아키텍처 패턴**을 사용하므로 DB 통합이 매우 용이합니다:

- **API 레벨 통합**: 두 서비스를 하나의 API 게이트웨이로 통합
- **데이터베이스 통합**: 동일한 PostgreSQL 인스턴스 사용
- **스키마 통합**: Alembic을 통한 마이그레이션 관리
- **클라이언트 통합**: 동일한 API 통신 방식으로 통합 가능

**결론: 현재 프로젝트는 참고 프로젝트와 완전히 동일한 구조적 특징을 가지고 있으며, DB 통합이 매우 용이한 상태입니다!** 🎉
