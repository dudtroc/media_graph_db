# 테스트 데이터

이 폴더는 Scene Graph Database의 테스트에 사용되는 샘플 데이터를 포함합니다.

## 파일 목록

- **Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.json**: 장면 그래프 메타데이터 (JSON 형식)
- **Kingdom_EP01_visual_2220-3134_(00_01_33-00_02_11)_meta_info.pt**: PyTorch 임베딩 벡터 데이터

## 사용법

테스트 실행 시 이 데이터를 사용하여 데이터베이스 기능을 검증합니다:

```bash
# 데이터베이스 테스트 실행
python tests/test_database.py

# API 테스트 실행 (서버 실행 후)
python tests/test_api.py
```

## 데이터 형식

### JSON 파일
- 장면 번호, 장소, 시간, 분위기 정보
- 객체, 이벤트, 공간/시간 관계 노드 정보

### PT 파일
- 384차원 임베딩 벡터
- 노드 ID와 매핑된 벡터 데이터


