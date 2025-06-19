# 채용공고 크롤러 서비스

## 📋 개요
원티드, 잡코리아, 사람인의 IT/개발/데이터 관련 채용공고를 자동으로 수집하여 MongoDB에 저장하는 크롤링 서비스입니다.

## 🏗️ 프로젝트 구조
```
crawler-service/
├── Dockerfile                    # Docker 이미지 빌드 설정
├── docker-compose.yml           # Docker 서비스 구성
├── crontab                      # 주기실행 cron 설정
├── .env.example                 # 환경변수 예시 파일
├── main.py                     # 메인 실행 스크립트
├── run_crawlers.sh            # 병렬 크롤러 실행 스크립트
├── pyproject.toml             # Poetry 의존성 관리
├── requirements.txt           # pip 의존성 (백업용)
├── config/
│   └── site_configs.py        # 사이트별 크롤링 설정
├── crawler/                   # 크롤러 모듈
│   ├── base_crawler.py        # 기본 크롤러 클래스
│   ├── crawler_factory.py     # 크롤러 팩토리
│   ├── wanted_crawler.py      # 원티드 크롤러
│   ├── saramin_crawler.py     # 사람인 크롤러
│   └── jobkorea_crawler.py    # 잡코리아 크롤러
├── models/
│   └── data_models.py         # 데이터 모델 정의
├── utils/                     # 유틸리티 모듈
│   ├── database.py            # DB 연결 관리
│   ├── position_normalizer.py # 직무 정규화
│   └── tech_stack_normalizer.py # 기술스택 정규화
└── logs/                      # 로그 파일 저장
```

## 🎯 주요 기능
- **다중 플랫폼 지원**: 원티드, 잡코리아, 사람인
- **정규화된 데이터**: 직무, 기술스택, 경력 등 일관된 형태로 저장
- **중복 제거**: URL 기반 중복 방지 및 MongoDB 인덱스 활용
- **병렬 처리**: 사이트별 독립적 크롤링
- **Docker 지원**: 컨테이너 환경에서 실행 가능
- **주기 실행**: cron을 통한 자동화 지원

## 🚀 빠른 시작

### 1. Docker Compose 사용 (권장)

#### 저장소 클론 및 설정
```bash
# 저장소 클론
git clone <repository-url>
cd crawler-service

# 필수 파일들 생성
# crontab 파일 생성 (위의 crontab 설정 참고)

# (선택) 환경변수 파일 생성 (.env)
echo "CRAWLER_SERVICE_MONGODB_URI=mongodb://your-mongodb-host:27017/job_crawler" > .env
```

#### 단발성 실행 (개발/테스트용)
```bash
# 특정 사이트만 실행
docker-compose run --rm crawler python main.py --site wanted

# 전체 크롤링
docker-compose run --rm crawler python main.py --site wanted --full

# 모든 사이트 병렬 실행
docker-compose run --rm crawler ./run_crawlers.sh

# 커스텀 MongoDB URI로 실행
CRAWLER_SERVICE_MONGODB_URI="mongodb://custom-host:27017/job_crawler" \
docker-compose run --rm crawler ./run_crawlers.sh
```

#### 주기적 실행 (운영용)
```bash
# 주기실행 크롤러 시작
docker-compose up -d crawler-cron

# 로그 확인
docker-compose logs -f crawler-cron

# 서비스 중단
docker-compose down
```

### 2. 로컬 환경 설정

#### 시스템 요구사항
- Python 3.12+
- Poetry (의존성 관리)
- MongoDB 접근 권한

#### 환경 준비
```bash
# 1. Poetry 설치 (없는 경우)
curl -sSL https://install.python-poetry.org | python3 -

# 또는 pip로 설치
pip install poetry

# 2. 저장소 클론
git clone <repository-url>
cd crawler-service

# 3. 프로젝트 의존성 설치
poetry install

# 4. Playwright 브라우저 설치
poetry run playwright install chromium

# 5. 환경변수 설정 파일 생성
cp .env.example .env
# .env 파일에서 MongoDB URI 수정
```

#### 환경변수 설정
```bash
# 방법 1: .env 파일 사용 (권장)
cp .env.example .env

# .env 파일 내용 수정
CRAWLER_SERVICE_MONGODB_URI=mongodb://your-mongodb-host:27017/job_crawler
LOG_LEVEL=INFO

# 방법 2: 직접 export
export CRAWLER_SERVICE_MONGODB_URI="mongodb://your-mongodb-host:27017/job_crawler"
export LOG_LEVEL="INFO"

# 인증이 필요한 경우
export CRAWLER_SERVICE_MONGODB_URI="mongodb://username:password@host:27017/job_crawler?authSource=admin"
```

#### Poetry 사용법
```bash
# 의존성 설치
poetry install

# 개발 의존성 포함 설치
poetry install --with dev

# 가상환경 정보 확인
poetry env info

# 가상환경 활성화
poetry shell

# 가상환경에서 실행 (shell 진입하지 않고)
poetry run python main.py --site wanted

# 의존성 추가
poetry add requests

# 개발 의존성 추가
poetry add --group dev pytest
```

#### 크롤링 실행
```bash
# Poetry 가상환경에서 실행

# 단일 사이트 크롤링
poetry run python main.py --site wanted

# 전체 크롤링
poetry run python main.py --site wanted --full

# MongoDB URI 직접 지정
poetry run python main.py --site wanted --mongodb-uri mongodb://your-host:27017/job_crawler

# 모든 사이트 병렬 실행
poetry run ./run_crawlers.sh

# 커스텀 MongoDB URI로 병렬 실행
./run_crawlers.sh normal mongodb://your-host:27017/job_crawler

# 로그 레벨 설정
poetry run python main.py --site wanted --log-level DEBUG
```

#### 가상환경 활성화 후 실행 (선택사항)
```bash
# Poetry shell 진입
poetry shell

# 이후 poetry run 없이 직접 실행 가능
python main.py --site wanted
./run_crawlers.sh

# shell 종료
exit
```

#### 개발 환경 설정
```bash
# 코드 포맷팅 (Black)
poetry run black .

# 테스트 실행
poetry run pytest

# 테스트 커버리지
poetry run pytest --cov=crawler

# 의존성 업데이트
poetry update

# requirements.txt 생성 (필요시)
poetry export -f requirements.txt --output requirements.txt
```

## 📖 상세 사용법

### 명령어 옵션
```bash
# 기본 사용법
python main.py --site <사이트명> [옵션]

# 옵션 설명
--site          : 크롤링할 사이트 (wanted, saramin, jobkorea)
--full          : 전체 크롤링 (기본값: 신규만)
--mongodb-uri   : MongoDB 연결 URI
--log-level     : 로그 레벨 (DEBUG, INFO, WARNING, ERROR)

# 예시
python main.py --site wanted --full --log-level DEBUG
```

### 병렬 실행 스크립트
```bash
# run_crawlers.sh 사용법
./run_crawlers.sh [mode] [mongodb_uri]

# mode: normal(기본값) | full
# mongodb_uri: MongoDB 연결 주소

# 예시
./run_crawlers.sh                                    # 기본 실행
./run_crawlers.sh full                              # 전체 크롤링
./run_crawlers.sh normal mongodb://remote:27017/   # 원격 DB
```

## ⏰ 주기적 실행 설정

### Docker 환경에서 cron 설정
```bash
# crontab 파일 내용 확인
cat crontab

# Docker Compose로 주기실행 서비스 시작
docker-compose up -d crawler-cron

# cron 로그 확인
docker-compose exec crawler-cron tail -f /app/logs/cron.log
```

### 로컬 환경에서 cron 설정
```bash
# crontab 편집
crontab -e

# 다음 내용 추가
0 9 * * * cd /path/to/crawler-service && ./run_crawlers.sh >> logs/cron.log 2>&1
0 18 * * * cd /path/to/crawler-service && ./run_crawlers.sh >> logs/cron.log 2>&1

# cron 서비스 상태 확인
sudo systemctl status cron
```

## 🗂️ 데이터 구조

수집된 채용공고는 다음 구조로 저장됩니다:

```json
{
  "_id": "ObjectId",
  "job_id": "platform_year_identifier",
  "job_url": "원본 URL",
  "platform": "wanted|saramin|jobkorea",
  "job_title": "채용공고 제목",
  "company": {
    "name": "회사명",
    "size": "회사 규모",
    "industry": "업종"
  },
  "location": {
    "raw_text": "원본 지역 정보",
    "city": "시/도",
    "district": "구/군"
  },
  "experience": {
    "raw_text": "원본 경력 정보",
    "min_years": 0,
    "max_years": 10
  },
  "position": {
    "raw_text": "원본 직무",
    "normalized": {
      "primary_category": "분류",
      "secondary_category": "세부분류",
      "is_data_role": true
    }
  },
  "tech_stack": {
    "raw_text": "원본 기술스택",
    "raw_list": ["Python", "SQL"]
  },
  "crawled_at": "크롤링 시간"
}
```

## ⚙️ 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `CRAWLER_SERVICE_MONGODB_URI` | `mongodb://localhost:27017/` | MongoDB 연결 URI |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `TZ` | `Asia/Seoul` | 시간대 설정 |

## 📊 모니터링 및 관리

### 로그 확인
```bash
# Docker 환경
docker-compose logs -f crawler-cron
docker-compose logs crawler

# 로컬 환경
tail -f logs/*/crawler_*.log
tail -f logs/cron.log

# 특정 사이트 로그만 확인
tail -f logs/*/crawler_wanted.log
```

### 데이터 확인
외부 MongoDB 관리 도구나 직접 연결하여 데이터를 확인하세요:
```bash
# 예시: MongoDB Compass 또는 mongo shell 사용
# 컬렉션: wanted_job_postings, saramin_job_postings, jobkorea_job_postings
```

### 프로세스 관리
```bash
# 실행 중인 크롤러 확인
ps aux | grep 'python main.py'

# 모든 크롤러 강제 종료
pkill -f 'python main.py'

# Docker 서비스 재시작
docker-compose restart crawler-cron

# Docker 이미지 재빌드 (코드 변경시)
docker-compose build --no-cache
```

## 🔧 개발 정보

### 크롤링 코드 구조
[[]]

### 기술 스택
- **언어**: Python 3.12
- **의존성 관리**: Poetry
- **웹 크롤링**: Requests, BeautifulSoup, Playwright
- **데이터베이스**: MongoDB, PyMongo
- **컨테이너화**: Docker, Docker Compose

### 확장 방법
새로운 플랫폼 추가시:
1. `crawler/` 디렉토리에 새 크롤러 클래스 생성
2. `JobCrawler` 기본 클래스 상속
3. `_get_job_urls()`, `_crawl_job_detail()` 메서드 구현
4. `config/site_configs.py`에 설정 추가
5. `CrawlerFactory`에 등록

## ⚠️ 주의사항 및 팁

### 실행 관련
- **MongoDB 연결**: 크롤러 실행 전 MongoDB 서버가 실행 중인지 확인
- **방화벽**: MongoDB 포트(기본 27017)가 열려있는지 확인
- **디스크 공간**: 로그 파일이 계속 쌓이므로 주기적 정리 필요
```bash
# 7일 이전 로그 파일 정리
find logs/ -name "*.log" -mtime +7 -delete
```

### 봇 차단 방지
- **딜레이 준수**: 각 사이트별 설정된 딜레이 시간 준수
- **IP 분산**: 가능하면 여러 IP에서 분산 실행
- **시간차 실행**: 3개 사이트 동시 실행보다는 시간차를 두고 실행
```bash
# 시간차를 둔 실행 예시
python main.py --site wanted && sleep 300 && \
python main.py --site saramin && sleep 300 && \
python main.py --site jobkorea
```

### 리소스 관리
- **메모리**: Playwright는 브라우저당 100-200MB 사용
- **CPU**: 병렬 실행시 CPU 사용량 급증 가능
- **네트워크**: 대량 크롤링시 네트워크 대역폭 고려

### 개발/운영 분리
```bash
# 개발환경 (적은 페이지)
export CRAWL_PAGES=3
python main.py --site wanted

# 운영환경 (전체 페이지)
python main.py --site wanted --full
```

### 에러 대응
```bash
# 특정 사이트가 실패하는 경우
python main.py --site wanted --log-level DEBUG

# Playwright 브라우저 재설치
poetry run playwright install --force chromium

# Docker 이미지 완전 재빌드
docker-compose build --no-cache

# 컨테이너 로그 실시간 확인
docker-compose logs -f crawler-cron
```

## 📝 라이선스
MIT License