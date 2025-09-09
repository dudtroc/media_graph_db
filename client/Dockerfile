FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치 (클라이언트 + 서버)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 서버 의존성 추가 설치
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    alembic==1.13.1 \
    pgvector==0.2.4 \
    python-dotenv==1.0.0 \
    pydantic==2.5.0

# 클라이언트 코드 복사
COPY . .

# 기본 명령어 (서버 + 클라이언트 실행)
CMD ["python", "start_client_with_server.py"]
