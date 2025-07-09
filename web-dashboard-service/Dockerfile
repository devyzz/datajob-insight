FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY web-dashboard-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# _common 폴더 복사 (공통 모듈)
COPY _common ./_common

# 애플리케이션 코드 복사
COPY web-dashboard-service/ .

EXPOSE 8501

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV DOCKER_ENV=true

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
