FROM python:3.11-slim

WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 클라이언트 코드 복사
COPY . .

# 기본 명령어 (테스트 실행)
CMD ["python", "run_tests.py"]
