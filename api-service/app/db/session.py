# api-service/app/db/session.py
from _common.config.settings import common_settings 

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging # 로깅 임포트

# SQLAlchemy 로깅 설정
# logging.basicConfig() # 주석 처리하거나 레벨 조정
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO) # INFO 레벨로 SQL 쿼리 로깅
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG) # DEBUG 레벨로 더 상세한 로깅 (파라미터, 결과셋 등)
logging.getLogger('sqlalchemy.orm').setLevel(logging.DEBUG) # ORM 관련 상세 로깅

SQLALCHEMY_DATABASE_URL = common_settings.DATABASE_URL 

# echo=True 또는 echo="debug" 옵션도 유사한 효과를 냅니다.
# engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
engine = create_engine(SQLALCHEMY_DATABASE_URL) # 기존 방식 유지하고 로거 사용

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()