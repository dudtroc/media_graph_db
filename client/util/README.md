# 클라이언트 유틸리티 모듈들

이 디렉토리는 장면그래프 데이터베이스 클라이언트의 핵심 기능들을 제공하는 유틸리티 모듈들을 포함합니다.

## 📁 모듈 구조

```
util/
├── __init__.py                    # 모듈 초기화 및 export
├── scene_graph_api_uploader.py   # 장면그래프 데이터 업로드
├── check_stored_data.py          # 저장된 데이터 확인
├── delete_video_data.py          # 비디오 데이터 삭제
└── README.md                     # 이 파일
```

## 🛠️ 모듈 설명

### 1. SceneGraphAPIUploader
**장면그래프 데이터를 API 서버에 업로드하는 모듈**

#### 주요 기능
- JSON 파일에서 장면그래프 데이터 읽기
- PT 파일에서 임베딩 데이터 읽기
- API를 통한 비디오, 장면, 노드 데이터 저장
- 파일명 자동 파싱 (드라마명, 에피소드, 프레임 범위)

#### 사용법
```python
from util.scene_graph_api_uploader import SceneGraphAPIUploader

uploader = SceneGraphAPIUploader()
success = uploader.upload_scene_graph("data/scene_data.json")
```

### 2. SceneGraphDataChecker
**저장된 장면그래프 데이터를 확인하는 모듈**

#### 주요 기능
- API 서버 연결 상태 확인
- 저장된 비디오 목록 조회
- 각 비디오의 장면 정보 확인
- 장면별 노드 데이터 확인 (객체, 이벤트, 관계, 임베딩)

#### 사용법
```python
from util.check_stored_data import SceneGraphDataChecker

checker = SceneGraphDataChecker()
checker.check_all_data()
```

### 3. VideoDataDeleter
**비디오 및 연결된 모든 데이터를 삭제하는 모듈**

#### 주요 기능
- 비디오 목록 조회
- 특정 비디오의 상세 정보 확인
- 안전한 삭제 (확인 절차 포함)
- CASCADE 삭제 (모든 관련 데이터 자동 삭제)

#### 사용법
```python
from util.delete_video_data import VideoDataDeleter

deleter = VideoDataDeleter()
success = deleter.delete_video(1001, confirm=True)
```

## 🚀 통합 사용

이 모듈들은 `SceneGraphClient`에서 통합되어 사용됩니다:

```python
from scene_graph_client import SceneGraphClient

# 모든 기능을 통합된 인터페이스로 사용
client = SceneGraphClient()
client.upload_scene_graph("data/scene.json")
client.check_all_data()
client.delete_video(1001)
```

## 📋 모듈 간 의존성

- **SceneGraphAPIUploader**: 독립적 (requests, torch, numpy 사용)
- **SceneGraphDataChecker**: 독립적 (requests 사용)
- **VideoDataDeleter**: 독립적 (requests 사용)

모든 모듈은 서로 독립적으로 작동하며, 공통적으로 `requests` 라이브러리를 사용하여 API 서버와 통신합니다.

## 🔧 개발 가이드

### 새로운 유틸리티 모듈 추가

1. 새로운 Python 파일을 `util/` 디렉토리에 생성
2. `__init__.py`에 새로운 클래스를 추가
3. `SceneGraphClient`에서 새로운 모듈을 import하여 사용

### 모듈 수정 시 주의사항

- 기존 API 인터페이스는 유지하여 하위 호환성 보장
- 새로운 기능 추가 시 `SceneGraphClient`에도 통합
- 에러 처리는 일관된 방식으로 구현

## 📚 관련 문서

- [메인 클라이언트 README](../README.md)
- [통합 클라이언트 사용 가이드](../CLIENT_USAGE.md)
- [API 서버 문서](../../server/README.md)
