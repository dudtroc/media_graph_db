# 데이터베이스 스키마 테스트 및 수정 가이드

## 📋 개요

이 디렉토리에는 데이터베이스 스키마를 확인하고 `start_frame`, `end_frame` 컬럼을 추가하는 테스트 스크립트들이 포함되어 있습니다.

## 🚀 스크립트 실행 방법

### 1. 빠른 스키마 확인 및 수정

```bash
python quick_schema_check.py
```

**기능:**
- scenes 테이블의 현재 컬럼 구조 확인
- 누락된 `start_frame`, `end_frame` 컬럼 자동 추가
- 간단한 테스트 데이터 삽입으로 검증

**출력 예시:**
```
🔍 빠른 스키마 확인 및 수정
========================================
✅ 데이터베이스 연결 성공

📋 scenes 테이블 현재 컬럼:
  - id: integer
  - video_id: integer
  - scene_number: character varying
  - scene_place: text
  - scene_time: character varying
  - scene_atmosphere: text
  - created_at: timestamp without time zone

⚠️  누락된 컬럼: ['start_frame', 'end_frame']
✅ start_frame 컬럼 추가 완료
✅ end_frame 컬럼 추가 완료
✅ 모든 컬럼 추가 완료

📋 수정된 scenes 테이블 컬럼:
  - id: integer
  - video_id: integer
  - scene_number: character varying
  - scene_place: text
  - scene_time: character varying
  - scene_atmosphere: text
  - start_frame: integer
  - end_frame: integer
  - created_at: timestamp without time zone

🧪 간단한 테스트:
✅ 테스트 장면 생성: ID 1
✅ 테스트 완료 및 데이터 정리
```

### 2. 상세한 스키마 테스트

```bash
python test_schema.py
```

**기능:**
- 모든 테이블의 상세한 스키마 정보 출력
- 데이터베이스 기본 정보 및 통계
- 누락된 컬럼 자동 추가
- 완전한 테스트 데이터 삽입 및 검증

**출력 예시:**
```
🚀 데이터베이스 스키마 테스트 시작
============================================================

📊 데이터베이스 정보:
==================================================
PostgreSQL 버전: PostgreSQL 15.1 (Debian 15.1-1.pgdg110+1)
데이터베이스 크기: 256 kB

테이블별 통계:
  - embeddings: INSERT=0, UPDATE=0, DELETE=0
  - events: INSERT=0, UPDATE=0, DELETE=0
  - objects: INSERT=0, UPDATE=0, DELETE=0
  - scenes: INSERT=0, UPDATE=0, DELETE=0
  - spatial: INSERT=0, UPDATE=0, DELETE=0
  - temporal: INSERT=0, UPDATE=0, DELETE=0
  - video: INSERT=0, UPDATE=0, DELETE=0

📋 데이터베이스의 모든 테이블:
==================================================
  - embeddings
  - events
  - objects
  - scenes
  - spatial
  - temporal
  - video

🔍 테이블 'video' 스키마:
----------------------------------------
컬럼명               타입            NULL     기본값           길이
----------------------------------------------------------------------
id                  integer         NO      nextval('video_id_seq') N/A
video_unique_id     integer         NO      NULL              N/A
drama_name          character varying YES     NULL              255
episode_number      character varying YES     NULL              50
created_at          timestamp without time zone YES     now()              N/A
updated_at          timestamp without time zone YES     now()              N/A

... (기타 테이블들도 동일한 형식으로 출력)
```

## 🔧 문제 해결

### 1. 데이터베이스 연결 실패

**오류:**
```
❌ 데이터베이스 연결 실패: connection to server at "localhost" (127.0.0.1) failed
```

**해결 방법:**
1. Docker 컨테이너가 실행 중인지 확인:
   ```bash
   docker-compose ps
   ```

2. 환경 변수 확인:
   ```bash
   cat .env
   ```

3. 컨테이너 내부에서 실행:
   ```bash
   docker exec -it <container_name> bash
   python quick_schema_check.py
   ```

### 2. 권한 오류

**오류:**
```
❌ start_frame 컬럼 추가 실패: permission denied for table scenes
```

**해결 방법:**
1. 데이터베이스 사용자 권한 확인
2. 슈퍼유저로 연결 시도
3. 테이블 소유권 확인

### 3. 컬럼이 이미 존재하는 경우

**출력:**
```
✅ 모든 필요한 컬럼이 존재합니다.
```

이는 정상적인 상황입니다. `start_frame`, `end_frame` 컬럼이 이미 추가되어 있다는 의미입니다.

## 📊 예상 결과

### 수정 전 (문제 상황)
```
📋 scenes 테이블 현재 컬럼:
  - id: integer
  - video_id: integer
  - scene_number: character varying
  - scene_place: text
  - scene_time: character varying
  - scene_atmosphere: text
  - created_at: timestamp without time zone

⚠️  누락된 컬럼: ['start_frame', 'end_frame']
```

### 수정 후 (정상 상황)
```
📋 수정된 scenes 테이블 컬럼:
  - id: integer
  - video_id: integer
  - scene_number: character varying
  - scene_place: text
  - scene_time: character varying
  - scene_atmosphere: text
  - start_frame: integer        ← 새로 추가됨
  - end_frame: integer          ← 새로 추가됨
  - created_at: timestamp without time zone

✅ 모든 필요한 컬럼이 존재합니다.
```

## 🎯 다음 단계

스키마 수정이 완료되면:

1. **업로더 재실행:**
   ```bash
   python run_uploader.py
   ```

2. **API 테스트:**
   ```bash
   curl -X GET "http://localhost:8000/health"
   ```

3. **데이터 확인:**
   ```bash
   curl -X GET "http://localhost:8000/videos"
   curl -X GET "http://localhost:8000/scenes"
   ```

## 📝 참고사항

- 이 스크립트들은 기존 데이터를 삭제하지 않습니다
- 테스트 데이터는 자동으로 정리됩니다
- `IF NOT EXISTS`를 사용하여 안전하게 컬럼을 추가합니다
- 모든 변경사항은 트랜잭션으로 처리됩니다
