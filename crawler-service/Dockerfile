# 크롤러 서비스 Dockerfile (Poetry 기반)
FROM python:3.12.3-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    # Playwright 브라우저 의존성
    wget \
    gnupg \
    ca-certificates \
    # 추가 도구
    cron \
    curl \
    git \
    # Playwright 브라우저 의존성
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry

# Poetry 설정
RUN poetry config virtualenvs.create false

# pyproject.toml과 poetry.lock 복사 (캐싱 최적화)
COPY pyproject.toml poetry.lock ./

# 의존성 설치 (운영 환경용)
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Playwright 브라우저 설치
RUN playwright install chromium && \
    playwright install-deps chromium

# 애플리케이션 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# 실행 스크립트 권한 설정
RUN chmod +x run_crawlers.sh

# 시간대 설정 (한국 시간)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pymongo; pymongo.MongoClient(timeout=1).admin.command('ping')" || exit 1

# 단발성 실행이 기본값
CMD ["python", "main.py", "--site", "wanted"]
