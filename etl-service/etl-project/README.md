# 목차
1. 설치 및 준비
2. Docker 환경 가이드 및 예제 코드

### 주요 파일  
- `.env`           — 환경변수 정의  
- `docker-compose.yml` — MongoDB·PostgreSQL 서비스 정의  
- `requirements.txt`  — 파이썬 라이브러리 목록  
- `etl.py`         — MongoDB → PostgreSQL ETL 스크립트  

## 1. 설치 및 준비

1. 저장소 클론  
   bash
   git clone https://github.com/your-org/datajob-insight.git
   cd datajob-insight/etl-service/etl-project

2. 환경변수 파일 생성
프로젝트 루트에 .env 파일을 만들고 아래 작성
#####
PGOPTIONS=-c client_encoding=UTF8 -c lc_messages=C

MONGO_URI=mongodb://root:example_pw@localhost:27017/jobdata?authSource=admin
MONGO_DB=jobdata

POSTGRES_SERVER=localhost
POSTGRES_USER=datajob_user
POSTGRES_PASSWORD=1234
POSTGRES_DB=datajob_test
POSTGRES_PORT=5432

PGCLIENTENCODING=UTF8
#####

3. 파이썬 의존성 설치
pip install --no-cache-dir -r requirements.txt

4. Docker 컨테이너 실행
docker-compose up -d

### 사용법
1. ETL 스크립트 실행
python etl.py

* .env 로드 → MongoDB에서 데이터 조회 → PostgreSQL에 upsert
* 콘솔에 삽입/업데이트 건수가 로그로 출력됩니다.

2. Docker Compose 명령어
* 로그 보기
docker-compose logs mongo_db
docker-compose logs postgres_db
* 서비스 중지 및 볼륨 삭제
docker-compose down -v

## 2. Docker 환경 가이드 및 예제 코드
* docker-compose.yml
version: "3.8"

services:
  mongo_db:
    image: mongo:6.0
    container_name: mongo_db
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example_pw
    ports:
      - "27017:27017"

  postgres_db:
    image: postgres:14
    container_name: postgres_db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"

volumes:
  pgdata:

* 설명
1. MongoDB
* mongo_db:27017 포트 매핑
* 루트 사용자 및 비밀번호 설정

2. PostgreSQL
* postgres_db:5432 포트 매핑
* ${POSTGRES_*} 환경변수를 통해 유연하게 설정

3. 볼륨
* pgdata 로 Postgres 데이터 영속화

## 3. 환경변수 설정 및 구성 옵션 설명
| 변수 이름               | 예시 값                                                                 | 설명                                          |
| ------------------- | -------------------------------------------------------------------- | ------------------------------------------- |
| `PGOPTIONS`         | `-c client_encoding=UTF8 -c lc_messages=C`                           | psycopg2의 클라이언트 인코딩·메시지 로케일 강제 설정           |
| `MONGO_URI`         | `mongodb://root:example_pw@localhost:27017/jobdata?authSource=admin` | MongoDB 연결 문자열 (사용자, 비밀번호, 호스트, DB 지정)      |
| `MONGO_DB`          | `jobdata`                                                            | MongoDB 내에서 사용할 데이터베이스 이름                   |
| `POSTGRES_SERVER`   | `localhost`                                                          | PostgreSQL 호스트 (컨테이너 내부 실행 시 `postgres_db`) |
| `POSTGRES_PORT`     | `5432`                                                               | PostgreSQL 포트                               |
| `POSTGRES_DB`       | `datajob_test`                                                       | PostgreSQL 데이터베이스 이름                        |
| `POSTGRES_USER`     | `datajob_user`                                                       | PostgreSQL 사용자명                             |
| `POSTGRES_PASSWORD` | `1234`                                                               | PostgreSQL 사용자 비밀번호                         |
| `PGCLIENTENCODING`  | `UTF8`                                                               | psycopg2 연결 시 사용할 문자 인코딩                    |
| `PGPASSFILE`        | `./.pgpass`                                                          | libpq가 참조하는 비밀번호 파일 경로 (일반적으로 제거 권장)        |
