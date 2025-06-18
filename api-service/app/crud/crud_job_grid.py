# api-service/app/crud/crud_job_grid.py
from sqlalchemy.orm import Session
from sqlalchemy import text # raw SQL 실행 및 search_path 확인을 위해 추가
from ..models.job_grid import JobGrid # JobGrid 모델을 정확히 임포트해야 합니다.
import logging

# 로거 설정 (애플리케이션 레벨에서 이미 설정되어 있다면 이 부분은 생략 가능)
# 간단한 테스트를 위해 기본 설정을 추가합니다.
# 실제 운영 환경에서는 FastAPI 앱의 로깅 설정을 따르거나 더 정교한 설정을 사용하세요.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) # 현재 모듈(__name__)의 로거를 사용

def get_job_grid(db: Session, skip: int = 0, limit: int = 100):
    try:
        # JobGrid 모델이 인식하는 스키마와 테이블 이름 로깅
        effective_schema = JobGrid.__table__.schema
        model_table_name = JobGrid.__table__.name # 모델에 정의된 테이블 이름
        logger.info(f"ORM model JobGrid is targeting schema: '{effective_schema}', table: '{model_table_name}'")

        # 현재 세션의 search_path 로깅
        try:
            search_path_result = db.execute(text("SHOW search_path")).scalar_one_or_none()
            logger.info(f"Current session search_path: {search_path_result}")
        except Exception as e_sp:
            logger.error(f"Error getting session search_path: {e_sp}", exc_info=True)

    except Exception as e_log_meta:
        logger.error(f"Error getting metadata for JobGrid model: {e_log_meta}", exc_info=True)
        # 메타데이터 로깅 실패 시에도 계속 진행하도록 model_table_name을 기본값으로 설정
        model_table_name = "JobPosting" # JobGrid 모델의 __tablename__과 일치시켜야 함

    logger.info(f"Attempting to query JobGrid table with skip={skip}, limit={limit}")
    try:
        # 1. ORM 쿼리 (기존 코드)
        result_orm = db.query(JobGrid).offset(skip).limit(limit).all()
        logger.info(f"ORM query successful. Number of records found: {len(result_orm)}")

        # ORM 결과가 0건일 경우 추가 디버깅 정보 로깅
        if not result_orm:
            # 2. ORM 쿼리로 전체 카운트 확인 (필터 없이)
            try:
                total_count_orm = db.query(JobGrid).count()
                logger.info(f"Total count from ORM query (no offset/limit): {total_count_orm}")
            except Exception as e_orm_count:
                logger.error(f"Error executing ORM count query: {e_orm_count}", exc_info=True)

            # 3. Raw SQL 쿼리로 직접 카운트 확인
            # model_table_name 변수를 사용하여 실제 테이블 이름을 참조
            try:
                raw_sql_count_query = text(f"SELECT COUNT(*) FROM {model_table_name}") # 스키마는 search_path에 의존
                count_result = db.execute(raw_sql_count_query).scalar_one()
                logger.info(f"Raw SQL COUNT(*) on table '{model_table_name}' returned: {count_result}")
            except Exception as raw_sql_err_count:
                logger.error(f"Error executing raw SQL COUNT(*) on table '{model_table_name}': {raw_sql_err_count}", exc_info=True)

            # 4. Raw SQL 쿼리로 실제 데이터 몇 개 가져오기 (데이터 확인용)
            try:
                raw_sql_select_query = text(f"SELECT * FROM {model_table_name} LIMIT 5") # 예시로 5개만
                sample_data = db.execute(raw_sql_select_query).fetchall()
                logger.info(f"Raw SQL SELECT * on table '{model_table_name}' (LIMIT 5) returned {len(sample_data)} rows.")
                # if sample_data:
                #     logger.info(f"First row from raw SQL: {sample_data[0]}") # 필요시 주석 해제
            except Exception as raw_sql_err_select:
                logger.error(f"Error executing raw SQL SELECT * on table '{model_table_name}': {raw_sql_err_select}", exc_info=True)
        
        return result_orm

    except Exception as e_main_query:
        logger.error(f"Error in get_job_grid function during main query execution: {e_main_query}", exc_info=True)
        return [] # 오류 발생 시 빈 리스트 반환