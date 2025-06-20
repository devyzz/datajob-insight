> docker version

> mkdir mongo-data

## 도커 몽고디비 세팅
> docker run -d --name my-mongo -p 27017:27017 -v %cd%\mongo-data:/data/db -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=secret123 mongo:latest

> docker ps ( up 확인 )

## 도커 몽고디비 접속
> docker exec -it my-mongo mongosh -u admin -p secret123 --authenticationDatabase admin

# use DATABASE_NAME

# db.createUser({user:"testuser1", pwd:"1234", roles:[{role:"readWrite",db:"jobdata"}]})

# exit

## ETL 세팅
> mkdir etl-project ( ETL용 서브 디렉터리 )

> cd etl-project

## 파이썬 가상환경 세팅 ( Power Shell )
> python -m venv .venv

> .\.venv\Scripts\Activate.ps1

(.venv) > python -m pip install --upgrade pip
(.venv) > python -m pip install pandas pymongo sqlalchemy psycopg2-binary python-dotenv

## etl-project 파일에서 .env파일 생성 후 아래 작성
# MongoDB 접속 정보
MONGO_URI=mongodb://jobuser:jobpass@localhost:27017/jobdata

# PostgreSQL 접속 정보
POSTGRES_URI=postgresql+psycopg2://pguser:pgpass@localhost:5432/jobdb

docker exec -it my-postgres psql -U pguser -d jobdb






