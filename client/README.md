# Scene Graph Database Client

장면그래프 데이터베이스 API 서버와 연동하여 데이터를 관리하는 클라이언트 도구들입니다.

## 📁 파일 구조

```
client/
├── scene_graph_client.py       # 통합 클라이언트 (NEW)
├── test_integrated_client.py   # 통합 클라이언트 테스트
├── util/                       # 유틸리티 모듈들
│   ├── __init__.py            # 모듈 초기화
│   ├── scene_graph_api_uploader.py # 장면그래프 데이터 업로드
│   ├── check_stored_data.py   # 저장된 데이터 확인
│   └── delete_video_data.py   # 비디오 데이터 삭제
├── data/                       # 테스트 데이터
│   ├── *.json                 # 장면그래프 JSON 파일
│   └── *.pt                   # 임베딩 PT 파일
├── requirements.txt           # 클라이언트 의존성
├── Dockerfile                 # 클라이언트 Docker 이미지
├── README.md                  # 이 파일
└── CLIENT_USAGE.md           # 통합 클라이언트 사용 가이드
```

## 🛠️ 클라이언트 도구들

### 0. 🎭 scene_graph_client.py (통합 클라이언트) ⭐ **NEW**
**모든 DB API 접근 기능을 통합한 클라이언트**

#### 기능
- 모든 기존 클라이언트 기능 통합
- 비디오, 장면, 노드 관리
- 장면그래프 업로드 및 검색
- 데이터 내보내기/가져오기
- 대화형 모드 지원

#### 사용법
```bash
# 대화형 모드
python scene_graph_client.py interactive

# 개별 명령어
python scene_graph_client.py check        # 데이터 확인
python scene_graph_client.py list         # 비디오 목록
python scene_graph_client.py summary      # 데이터 요약

# Python 코드로 사용
python -c "
from scene_graph_client import SceneGraphClient
client = SceneGraphClient()
client.check_all_data()
"
```

#### 주요 메서드
- `health_check()` - API 서버 연결 확인
- `get_videos()` - 비디오 목록 조회
- `upload_scene_graph()` - 장면그래프 업로드
- `vector_search()` - 벡터 검색
- `export_scene_data()` - 데이터 내보내기

#### 상세 사용법
[CLIENT_USAGE.md](./CLIENT_USAGE.md) 참조

---

### 1. 📤 scene_graph_api_uploader.py
**장면그래프 데이터를 API 서버에 업로드하는 도구**

#### 기능
- JSON 파일에서 장면그래프 데이터 읽기
- PT 파일에서 임베딩 데이터 읽기
- API를 통한 비디오, 장면, 노드 데이터 저장
- 파일명 자동 파싱 (드라마명, 에피소드, 프레임 범위)

#### 사용법
```bash
# 기본 실행 (테스트 데이터 사용)
python scene_graph_api_uploader.py

# 특정 파일 업로드
python -c "
from util.scene_graph_api_uploader import SceneGraphAPIUploader
uploader = SceneGraphAPIUploader()
uploader.upload_scene_graph('data/your_file.json')
"
```

#### 지원 파일 형식
- **JSON 파일**: `{drama_name}_{episode}_{visual}_{start_frame}-{end_frame}_{timestamp}_meta_info.json`
- **PT 파일**: `{drama_name}_{episode}_{visual}_{start_frame}-{end_frame}_{timestamp}_meta_info.pt`

#### 예시
```bash
# Kingdom EP01 데이터 업로드
python scene_graph_api_uploader.py
# → data/Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json 사용
```

---

### 2. 🔍 check_stored_data.py
**저장된 장면그래프 데이터를 확인하는 도구**

#### 기능
- API 서버 연결 상태 확인
- 저장된 비디오 목록 조회
- 각 비디오의 장면 정보 확인
- 장면별 노드 데이터 확인 (객체, 이벤트, 관계, 임베딩)

#### 사용법
```bash
# 전체 데이터 확인
python check_stored_data.py

# Python 코드로 사용
python -c "
from util.check_stored_data import SceneGraphDataChecker
checker = SceneGraphDataChecker()
checker.check_all_data()
"
```

#### 출력 예시
```
🔍 저장된 장면그래프 데이터 확인
============================================================
✅ API 서버 연결 성공

📺 저장된 비디오 목록:
  - Kingdom EP01 (ID: 2, Unique ID: 1001)

🎭 비디오 'Kingdom EP01'의 장면들:
  📍 장면 ID: 1
     - 장면 번호: SC001
     - 프레임: 1000-2000
     - 장소: 테스트 장소
     
     👥 객체 노드 (1개):
       - 주인공 (ID: OBJ001, 타입: character)
     
     🎬 이벤트 노드 (1개):
       - walk (ID: EVT001, 주체: OBJ001)
```

---

### 3. 🗑️ delete_video_data.py
**비디오 및 연결된 모든 데이터를 삭제하는 도구**

#### 기능
- 비디오 목록 조회
- 특정 비디오의 상세 정보 확인
- 안전한 삭제 (확인 절차 포함)
- CASCADE 삭제 (모든 관련 데이터 자동 삭제)

#### 사용법
```bash
# 대화형 모드 (안전한 삭제)
python delete_video_data.py

# 비디오 목록만 표시
python delete_video_data.py list

# 특정 비디오 삭제 (확인 필요)
python delete_video_data.py 1001

# 확인 없이 삭제 (자동화용)
python delete_video_data.py 1001 --yes
```

#### 삭제되는 데이터
- 비디오 정보
- 연결된 모든 장면
- 장면의 모든 노드 (객체, 이벤트, 공간관계, 시간관계)
- 모든 임베딩 데이터

#### 안전 기능
- 삭제 전 상세 정보 표시
- 사용자 확인 절차
- 삭제된 데이터 종류와 수량 표시

---

## 🚀 빠른 시작

### 1. 통합 클라이언트 사용 (권장)
```bash
# 클라이언트 컨테이너 접속
docker exec -it scene_graph_client_test bash

# 통합 클라이언트 대화형 모드
python scene_graph_client.py interactive

# 또는 개별 명령어
python scene_graph_client.py check        # 데이터 확인
python scene_graph_client.py list         # 비디오 목록
python scene_graph_client.py summary      # 데이터 요약
```

### 2. Docker 환경에서 개별 도구 사용
```bash
# 클라이언트 컨테이너 접속
docker exec -it scene_graph_client_test bash

# 데이터 업로드
python util/scene_graph_api_uploader.py

# 데이터 확인
python util/check_stored_data.py

# 데이터 삭제
python util/delete_video_data.py
```

### 3. 로컬 환경에서 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export API_URL="http://localhost:8000"

# 통합 클라이언트 사용
python scene_graph_client.py interactive

# 또는 개별 도구 실행
python util/scene_graph_api_uploader.py
python util/check_stored_data.py
python util/delete_video_data.py
```

## ⚙️ 환경 설정

### 환경 변수
- `API_URL`: API 서버 URL (기본값: `http://localhost:8000`)
- `DOCKER_CONTAINER`: Docker 환경 여부 (선택사항)

### 의존성
```txt
requests==2.31.0
python-dotenv==1.0.0
numpy==1.24.3
torch==2.1.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
alembic==1.13.1
```

## 📊 데이터 흐름

```
JSON/PT 파일 → scene_graph_api_uploader.py → API 서버 → 데이터베이스
                                                      ↓
check_stored_data.py ← API 서버 ← 데이터베이스
                                                      ↓
delete_video_data.py → API 서버 → 데이터베이스 (삭제)
```

## 🔧 고급 사용법

### 1. 커스텀 API URL 사용
```python
from scene_graph_api_uploader import SceneGraphAPIUploader
from check_stored_data import SceneGraphDataChecker
from delete_video_data import VideoDataDeleter

# 다른 서버 사용
uploader = SceneGraphAPIUploader("http://192.168.1.100:8000")
checker = SceneGraphDataChecker("http://192.168.1.100:8000")
deleter = VideoDataDeleter("http://192.168.1.100:8000")
```

### 2. 프로그래밍 방식 사용
```python
# 데이터 업로드
uploader = SceneGraphAPIUploader()
success = uploader.upload_scene_graph("data/my_scene.json")

# 데이터 확인
checker = SceneGraphDataChecker()
videos = checker.get_videos()
for video in videos:
    print(f"비디오: {video['drama_name']} {video['episode_number']}")

# 데이터 삭제
deleter = VideoDataDeleter()
success = deleter.delete_video(1001, confirm=True)
```

### 3. 배치 처리
```bash
# 여러 비디오 삭제
for video_id in 1001 1002 1003; do
    python delete_video_data.py $video_id --yes
done

# 데이터 확인 후 정리
python check_stored_data.py
python delete_video_data.py list
```

## 🐛 문제 해결

### 일반적인 문제
1. **API 서버 연결 실패**: 서버가 실행 중인지 확인
2. **파일을 찾을 수 없음**: 올바른 경로에 파일이 있는지 확인
3. **권한 오류**: 파일 읽기/쓰기 권한 확인

### 로그 확인
```bash
# Docker 환경에서 로그 확인
docker-compose logs api_server
docker-compose logs client_test
```

## 📚 추가 정보

- [메인 프로젝트 README](../README.md)
- [API 서버 문서](../server/README.md)
- [데이터베이스 스키마](../server/models/orm_models.py)

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해 주세요.
