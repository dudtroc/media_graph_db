# SceneGraphClient 사용 가이드

## 개요

`SceneGraphClient`는 장면그래프 데이터베이스의 모든 기능을 통합한 클라이언트 클래스입니다. 기존의 개별 클라이언트들(`VideoDataDeleter`, `SceneGraphDataChecker`, `SceneGraphAPIUploader`)의 기능을 하나로 통합하여 더 편리하게 사용할 수 있습니다.

## 주요 기능

### 1. 기본 연결 및 상태 확인
- API 서버 헬스 체크
- 서버 기본 정보 조회

### 2. 비디오 관리
- 비디오 목록 조회
- 비디오 정보 조회
- 비디오 생성
- 비디오 삭제

### 3. 장면 관리
- 장면 목록 조회
- 장면 그래프 정보 조회
- 객체, 이벤트, 관계 노드 조회
- 임베딩 정보 조회

### 4. 장면그래프 업로드
- JSON 파일에서 장면그래프 데이터 업로드
- PT 파일과 함께 업로드

### 5. 검색 기능
- 벡터 기반 유사도 검색
- 하이브리드 검색 (텍스트 + 벡터)

### 6. 데이터 관리
- 전체 데이터 확인
- 데이터 요약 정보 조회
- 장면 데이터 내보내기/가져오기
- 데이터 삭제 (개별/전체)

### 7. 데이터 삭제 도구
- 전체 데이터 삭제
- 특정 비디오 삭제
- 드라마별 삭제
- 안전한 삭제 (확인 절차)

## 사용법

### 기본 사용법

```python
from scene_graph_client import SceneGraphClient

# 클라이언트 초기화
client = SceneGraphClient("http://localhost:8000")

# API 서버 연결 확인
if client.health_check():
    print("서버 연결 성공!")
```

### 1. 데이터 확인

```python
# 모든 데이터 확인
client.check_all_data()

# 데이터 요약 정보
summary = client.get_data_summary()
print(f"총 비디오: {summary['total_videos']}개")
print(f"총 장면: {summary['total_scenes']}개")
```

### 2. 비디오 관리

```python
# 비디오 목록 조회
videos = client.get_videos()
for video in videos:
    print(f"{video['drama_name']} {video['episode_number']}")

# 특정 비디오 정보 조회
video_info = client.get_video_info(1001)
print(f"장면 수: {video_info['scene_count']}")

# 비디오 생성
new_video = client.create_video("Kingdom", "EP02", 1002)

# 비디오 삭제
client.delete_video(1001, confirm=True)
```

### 3. 장면 관리

```python
# 장면 목록 조회
scenes = client.get_scenes(video_id=1)

# 장면 그래프 정보 조회
scene_graph = client.get_scene_graph(scene_id=1)
print(f"객체 수: {len(scene_graph['objects'])}")
print(f"이벤트 수: {len(scene_graph['events'])}")

# 특정 노드 타입 조회
objects = client.get_scene_objects(scene_id=1)
events = client.get_scene_events(scene_id=1)
spatial = client.get_scene_spatial_relations(scene_id=1)
temporal = client.get_scene_temporal_relations(scene_id=1)
embeddings = client.get_scene_embeddings(scene_id=1)
```

### 4. 장면그래프 업로드

```python
# JSON 파일에서 업로드
success = client.upload_scene_graph("data/scene_data.json")

# PT 파일과 함께 업로드 (파일명이 일치해야 함)
success = client.upload_scene_graph_with_pt("data/scene_data.json", "data/scene_data.pt")
```

### 5. 검색 기능

```python
# 벡터 검색
query_vector = [0.1, 0.2, ...]  # 384차원 벡터
results = client.vector_search(
    query_embedding=query_vector,
    node_type="object",
    top_k=5
)

# 하이브리드 검색
results = client.hybrid_search(
    query_text="사람이 걷다",
    query_embedding=query_vector,
    node_type="event",
    top_k=10
)
```

### 6. 데이터 내보내기/가져오기

```python
# 장면 데이터 내보내기
client.export_scene_data(scene_id=1, output_file="scene_1.json")

# 장면 데이터 가져오기
client.import_scene_data("scene_1.json")
```

### 7. 데이터 삭제

```python
# 특정 비디오 삭제 (확인 필요)
success = client.delete_video(1001)

# 확인 없이 비디오 삭제
success = client.delete_video(1001, confirm=True)

# 비디오 목록 조회
client.list_videos()
```

## 명령행 사용법

### 대화형 모드

```bash
python scene_graph_client.py interactive
```

### 개별 명령어

```bash
# 데이터 확인
python scene_graph_client.py check

# 비디오 목록
python scene_graph_client.py list

# 데이터 요약
python scene_graph_client.py summary
```

### 데이터 삭제 도구

```bash
# 현재 상태 확인
python client_test_clear_all_data.py --status

# 모든 데이터 삭제 (확인 필요)
python client_test_clear_all_data.py --all

# 확인 없이 모든 데이터 삭제
python client_test_clear_all_data.py --all --yes

# 특정 비디오들만 삭제
python client_test_clear_all_data.py --videos 1001 1002 1003

# 대화형 모드
python client_test_clear_all_data.py
```

## 대화형 모드 명령어

### SceneGraphClient 대화형 모드
다음 명령어들을 사용할 수 있습니다:

1. **check** - 모든 데이터 확인
2. **list** - 비디오 목록 표시
3. **delete** - 비디오 삭제
4. **upload** - 장면그래프 업로드
5. **search** - 벡터 검색
6. **summary** - 데이터 요약
7. **quit** - 종료

### 데이터 삭제 도구 대화형 모드
`python client_test_clear_all_data.py` 실행 시:

1. **status** - 현재 상태 확인
2. **clear-all** - 모든 데이터 삭제
3. **clear-videos** - 특정 비디오 삭제
4. **quit** - 종료

## 환경 설정

### 환경 변수

```bash
# .env 파일 또는 환경 변수로 설정
export API_URL="http://localhost:8000"
```

### Docker 환경에서 사용

```bash
# 클라이언트 컨테이너 접속
docker exec -it scene_graph_client_test bash

# 통합 클라이언트 실행
python scene_graph_client.py interactive
```

## 예시 시나리오

### 1. 새로운 드라마 데이터 업로드

```python
from scene_graph_client import SceneGraphClient

client = SceneGraphClient()

# 1. 데이터 업로드
success = client.upload_scene_graph("data/Kingdom_EP01_scene.json")
if success:
    print("업로드 성공!")

# 2. 업로드된 데이터 확인
client.check_all_data()

# 3. 데이터 요약
summary = client.get_data_summary()
print(f"업로드된 장면: {summary['total_scenes']}개")
```

### 2. 특정 장면 분석

```python
# 1. 장면 그래프 조회
scene_graph = client.get_scene_graph(scene_id=1)

# 2. 객체 분석
objects = scene_graph['objects']
for obj in objects:
    print(f"객체: {obj['label']} (타입: {obj['type_of']})")

# 3. 이벤트 분석
events = scene_graph['events']
for event in events:
    print(f"이벤트: {event['verb']} (주체: {event['subject_id']})")

# 4. 임베딩 정보
embeddings = scene_graph['embeddings']
for emb in embeddings:
    print(f"임베딩: {emb['node_id']} (차원: {len(emb['embedding'])})")
```

### 3. 유사 장면 검색

```python
# 1. 검색할 벡터 준비 (384차원)
query_vector = [0.1, 0.2, ...]  # 실제 벡터로 교체

# 2. 벡터 검색
similar_objects = client.vector_search(
    query_embedding=query_vector,
    node_type="object",
    top_k=5
)

# 3. 결과 출력
for result in similar_objects:
    print(f"유사 객체: {result['label']} (유사도: {result['similarity']:.3f})")
```

### 4. 데이터 삭제

```python
# 1. 현재 데이터 상태 확인
summary = client.get_data_summary()
print(f"현재 비디오: {summary['total_videos']}개")

# 2. 특정 비디오 삭제
success = client.delete_video(1001, confirm=True)
if success:
    print("비디오 삭제 완료!")

# 3. 모든 데이터 삭제 (주의!)
videos = client.get_videos()
for video in videos:
    client.delete_video(video['video_unique_id'], confirm=True)
    print(f"삭제 완료: {video['drama_name']} {video['episode_number']}")

# 4. 최종 확인
final_summary = client.get_data_summary()
print(f"삭제 후 비디오: {final_summary['total_videos']}개")
```

### 5. 대량 데이터 관리

```python
# 1. 드라마별 데이터 정리
videos = client.get_videos()
drama_groups = {}
for video in videos:
    drama = video['drama_name']
    if drama not in drama_groups:
        drama_groups[drama] = []
    drama_groups[drama].append(video)

# 2. 특정 드라마의 모든 에피소드 삭제
target_drama = "Kingdom"
if target_drama in drama_groups:
    for video in drama_groups[target_drama]:
        client.delete_video(video['video_unique_id'], confirm=True)
        print(f"삭제: {video['drama_name']} {video['episode_number']}")

# 3. 데이터 백업 (내보내기)
for video in videos[:3]:  # 처음 3개만 백업
    scenes = client.get_scenes(video['id'])
    for scene in scenes:
        client.export_scene_data(scene['id'], f"backup_scene_{scene['id']}.json")
```

## 주의사항

1. **파일명 규칙**: JSON 파일과 PT 파일의 이름이 일치해야 합니다.
   - 예: `Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json`
   - 예: `Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.pt`

2. **벡터 차원**: 검색 시 사용하는 벡터는 384차원이어야 합니다.

3. **API 서버**: 사용 전에 API 서버가 실행 중인지 확인하세요.

4. **데이터 삭제**: 비디오 삭제 시 모든 관련 데이터가 함께 삭제되므로 주의하세요.
5. **대량 삭제**: `--yes` 옵션 사용 시 확인 없이 삭제되므로 신중하게 사용하세요.
6. **백업**: 중요한 데이터 삭제 전에는 반드시 백업을 수행하세요.

## 문제 해결

### 연결 오류
```python
if not client.health_check():
    print("API 서버에 연결할 수 없습니다.")
    print("서버가 실행 중인지 확인하세요.")
```

### 파일 업로드 오류
```python
import os

if not os.path.exists(json_file):
    print("파일을 찾을 수 없습니다.")
else:
    success = client.upload_scene_graph(json_file)
    if not success:
        print("업로드에 실패했습니다.")
```

### 검색 결과 없음
```python
results = client.vector_search(query_vector, top_k=5)
if not results:
    print("검색 결과가 없습니다.")
    print("벡터 차원이나 노드 타입을 확인하세요.")
```

### 데이터 삭제 오류
```python
# 삭제 실패 시 확인
videos = client.get_videos()
if not videos:
    print("삭제할 비디오가 없습니다.")
else:
    for video in videos:
        success = client.delete_video(video['video_unique_id'], confirm=True)
        if not success:
            print(f"삭제 실패: {video['drama_name']} {video['episode_number']}")

# 삭제 후 상태 확인
final_summary = client.get_data_summary()
if final_summary['total_videos'] > 0:
    print("일부 데이터가 남아있습니다.")
    print("수동으로 다시 삭제를 시도하세요.")
```

### 대량 삭제 시 주의사항
```python
# 안전한 대량 삭제
videos = client.get_videos()
print(f"총 {len(videos)}개의 비디오가 있습니다.")

# 배치 단위로 삭제 (한 번에 10개씩)
batch_size = 10
for i in range(0, len(videos), batch_size):
    batch = videos[i:i+batch_size]
    print(f"배치 {i//batch_size + 1}: {len(batch)}개 처리 중...")
    
    for video in batch:
        success = client.delete_video(video['video_unique_id'], confirm=True)
        if success:
            print(f"  ✅ {video['drama_name']} {video['episode_number']}")
        else:
            print(f"  ❌ {video['drama_name']} {video['episode_number']}")
    
    # 배치 간 잠시 대기
    import time
    time.sleep(1)
```

## 🛠️ 추가 도구들

### 1. client_test_clear_all_data.py - 데이터 삭제 도구
전체 데이터베이스의 모든 데이터를 안전하게 삭제하는 전용 도구입니다.

#### 주요 기능
- **전체 데이터 삭제**: 모든 비디오와 관련 데이터 일괄 삭제
- **선택적 삭제**: 특정 비디오 ID들만 삭제
- **안전한 삭제**: 사용자 확인 절차 포함
- **진행 상황 표시**: 실시간 삭제 진행률 표시
- **상태 확인**: 삭제 전후 데이터베이스 상태 확인

#### 사용법
```bash
# 현재 상태 확인
python client_test_clear_all_data.py --status

# 모든 데이터 삭제 (확인 필요)
python client_test_clear_all_data.py --all

# 확인 없이 모든 데이터 삭제
python client_test_clear_all_data.py --all --yes

# 특정 비디오들만 삭제
python client_test_clear_all_data.py --videos 1001 1002 1003

# 대화형 모드
python client_test_clear_all_data.py
```

### 2. example_clear_data.py - 사용 예시 스크립트
다양한 데이터 삭제 방법을 보여주는 예시 스크립트입니다.

#### 주요 기능
- **모든 데이터 삭제 예시**: 전체 데이터 삭제 과정 시연
- **선택적 삭제 예시**: 특정 비디오들만 삭제하는 방법
- **드라마별 삭제 예시**: 특정 드라마의 모든 에피소드 삭제
- **대화형 예시**: 사용자가 직접 선택하여 실행

#### 사용법
```bash
# 예시 스크립트 실행
python example_clear_data.py

# 선택 가능한 예시들:
# 1. 모든 데이터 삭제
# 2. 특정 비디오들만 삭제 (처음 3개)
# 3. 드라마 이름으로 삭제 (Kingdom)
# 4. 현재 상태만 확인
# 5. 종료
```

### 3. client_test_integrated_client.py - 통합 클라이언트 테스트
SceneGraphClient의 모든 기능을 테스트하는 스크립트입니다.

#### 주요 기능
- **기본 연결 테스트**: API 서버 연결 및 헬스 체크
- **비디오 관리 테스트**: 비디오 목록 조회 및 정보 조회
- **장면 관리 테스트**: 장면 그래프 정보 조회
- **데이터 요약 테스트**: 데이터베이스 요약 정보 조회
- **내보내기/가져오기 테스트**: 장면 데이터 내보내기 기능

#### 사용법
```bash
# 통합 테스트 실행
python client_test_integrated_client.py

# 테스트 결과 예시:
# 🧪 SceneGraphClient 통합 테스트
# ==================================================
# ✅ 기본 연결 테스트 통과
# ✅ 비디오 관리 테스트 통과
# ✅ 장면 관리 테스트 통과
# ✅ 데이터 요약 테스트 통과
# ✅ 내보내기/가져오기 테스트 통과
# 🎉 모든 테스트가 성공적으로 완료되었습니다!
```

## 📚 도구별 사용 시나리오

### 개발/테스트 환경
```bash
# 1. 데이터 초기화
python client_test_clear_all_data.py --all --yes

# 2. 테스트 데이터 업로드
python scene_graph_client.py interactive

# 3. 기능 테스트
python client_test_integrated_client.py
```

### 프로덕션 환경
```bash
# 1. 현재 상태 확인
python client_test_clear_all_data.py --status

# 2. 안전한 삭제 (확인 필요)
python client_test_clear_all_data.py --all

# 3. 특정 데이터만 삭제
python client_test_clear_all_data.py --videos 1001 1002
```

### 데이터 마이그레이션
```bash
# 1. 기존 데이터 백업
python scene_graph_client.py interactive
# → export_scene_data() 사용

# 2. 데이터 삭제
python client_test_clear_all_data.py --all --yes

# 3. 새 데이터 업로드
python scene_graph_client.py interactive
# → upload_scene_graph() 사용
```
