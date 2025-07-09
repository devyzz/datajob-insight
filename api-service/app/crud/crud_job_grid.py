# api-service/app/crud/crud_job_grid.py
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case
from ..models.job_grid import JobGrid # JobGrid 모델을 정확히 임포트해야 합니다.
import logging
from typing import Dict, List, Any

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

def get_job_stats_overview(db: Session) -> Dict[str, Any]:
    """전체 통계 개요를 반환합니다."""
    try:
        total_jobs = db.query(JobGrid).count()
        data_jobs = db.query(JobGrid).filter(JobGrid.is_data_job == True).count()
        non_data_jobs = total_jobs - data_jobs
        
        # 경력별 통계
        experience_stats = db.query(
            func.count(case((JobGrid.experience_min == '신입', 1))).label('신입'),
            func.count(case((JobGrid.experience_min.like('%년%'), 1))).label('경력')
        ).first()
        
        return {
            "total_jobs": total_jobs,
            "data_jobs": data_jobs,
            "non_data_jobs": non_data_jobs,
            "data_job_ratio": round(data_jobs / total_jobs * 100, 2) if total_jobs > 0 else 0,
            "experience_stats": {
                "신입": experience_stats.신입,
                "경력": experience_stats.경력
            }
        }
    except Exception as e:
        logger.error(f"Error in get_job_stats_overview: {e}")
        return {}

def get_tech_stack_stats(db: Session) -> List[Dict[str, Any]]:
    """기술 스택별 통계를 반환합니다."""
    try:
        # 기술 스택을 쉼표로 분리하여 개별 기술별로 카운트
        tech_stacks = db.query(JobGrid.tech_stack).filter(JobGrid.tech_stack.isnot(None)).all()
        
        tech_counter = {}
        for tech_stack in tech_stacks:
            if tech_stack[0]:
                techs = [tech.strip() for tech in tech_stack[0].replace('/', ',').replace(' ', ',').split(',') if tech.strip()]
                for tech in techs:
                    tech_counter[tech] = tech_counter.get(tech, 0) + 1
        
        # 상위 20개 기술만 반환
        sorted_techs = sorted(tech_counter.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return [{"tech_name": tech, "count": count} for tech, count in sorted_techs]
    except Exception as e:
        logger.error(f"Error in get_tech_stack_stats: {e}")
        return []

def get_position_stats(db: Session) -> List[Dict[str, Any]]:
    """포지션별 통계를 반환합니다."""
    try:
        position_stats = db.query(
            JobGrid.position,
            func.count(JobGrid.posting_id).label('count')
        ).group_by(JobGrid.position).order_by(func.count(JobGrid.posting_id).desc()).all()
        
        return [{"position": pos, "count": count} for pos, count in position_stats if pos]
    except Exception as e:
        logger.error(f"Error in get_position_stats: {e}")
        return []

def get_company_size_stats(db: Session) -> List[Dict[str, Any]]:
    """기업 규모별 통계를 반환합니다."""
    try:
        # company 테이블과 조인하여 company_size 정보 가져오기
        from sqlalchemy import text
        
        company_stats_query = text("""
            SELECT 
                c.company_size,
                COUNT(j.posting_id) as count,
                AVG(CASE 
                    WHEN j.experience_min = '신입' THEN 0
                    WHEN j.experience_min LIKE '%년%' THEN 
                        CAST(REGEXP_REPLACE(j.experience_min, '[^0-9]', '', 'g') AS INTEGER)
                    ELSE 0
                END) as avg_experience
            FROM jobposting j
            LEFT JOIN company c ON j.company_id = c.company_id
            GROUP BY c.company_size
            ORDER BY count DESC
        """)
        
        result = db.execute(company_stats_query)
        company_stats = result.fetchall()
        
        return [{"company_size": size, "count": count, "avg_experience": float(avg_exp) if avg_exp else 0} 
                for size, count, avg_exp in company_stats if size]
    except Exception as e:
        logger.error(f"Error in get_company_size_stats: {e}")
        return []

def get_data_job_stats(db: Session) -> List[Dict[str, Any]]:
    """데이터 직군 통계를 반환합니다."""
    try:
        data_job_stats = db.query(
            JobGrid.is_data_job,
            func.count(JobGrid.posting_id).label('count'),
            func.avg(case(
                (JobGrid.experience_min == '신입', 0),
                (JobGrid.experience_min.like('%년%'), 
                 func.cast(func.regexp_replace(JobGrid.experience_min, '[^0-9]', '', 'g'), func.Integer))
            )).label('avg_experience')
        ).group_by(JobGrid.is_data_job).all()
        
        return [{"is_data_job": is_data, "count": count, "avg_experience": float(avg_exp) if avg_exp else 0} 
                for is_data, count, avg_exp in data_job_stats]
    except Exception as e:
        logger.error(f"Error in get_data_job_stats: {e}")
        return []

def get_experience_stats(db: Session) -> List[Dict[str, Any]]:
    """경력별 통계를 반환합니다."""
    try:
        # 경력 분류
        experience_stats = db.query(
            case(
                (JobGrid.experience_min == '신입', '신입'),
                (JobGrid.experience_min.like('%1년%'), '1년'),
                (JobGrid.experience_min.like('%2년%'), '2년'),
                (JobGrid.experience_min.like('%3년%'), '3년'),
                (JobGrid.experience_min.like('%4년%'), '4년'),
                (JobGrid.experience_min.like('%5년%'), '5년'),
                (JobGrid.experience_min.like('%6년%'), '6년'),
                (JobGrid.experience_min.like('%7년%'), '7년'),
                (JobGrid.experience_min.like('%8년%'), '8년'),
                (JobGrid.experience_min.like('%9년%'), '9년'),
                (JobGrid.experience_min.like('%10년%'), '10년+'),
                else_='기타'
            ).label('experience_level'),
            func.count(JobGrid.posting_id).label('count')
        ).group_by('experience_level').order_by(func.count(JobGrid.posting_id).desc()).all()
        
        return [{"experience_level": level, "count": count} for level, count in experience_stats if level]
    except Exception as e:
        logger.error(f"Error in get_experience_stats: {e}")
        return []

def get_location_stats(db: Session) -> List[Dict[str, Any]]:
    """지역별 통계를 반환합니다."""
    try:
        # location에서 구 정보 추출 (SQL에서 처리)
        location_stats = db.query(
            func.split_part(JobGrid.location, ' ', 2).label('district'),
            func.count(JobGrid.posting_id).label('count')
        ).filter(JobGrid.location.isnot(None)).group_by('district').order_by(func.count(JobGrid.posting_id).desc()).all()
        
        return [{"district": district, "count": count} for district, count in location_stats if district]
    except Exception as e:
        logger.error(f"Error in get_location_stats: {e}")
        return []

def get_job_grid_with_company_info(db: Session, skip: int = 0, limit: int = 100):
    """company 정보가 포함된 job 데이터를 반환합니다."""
    try:
        from sqlalchemy import text
        
        job_query = text("""
            SELECT 
                j.*,
                c.company_size,
                c.company_name
            FROM jobposting j
            LEFT JOIN company c ON j.company_id = c.company_id
            ORDER BY j.posting_id
            LIMIT :limit OFFSET :skip
        """)
        
        result = db.execute(job_query, {"limit": limit, "skip": skip})
        job_data = result.fetchall()
        
        # 결과를 딕셔너리 리스트로 변환
        jobs = []
        for row in job_data:
            job_dict = {
                "posting_id": row[0],
                "company_id": row[1],
                "platform_id": row[2],
                "title": row[3],
                "job_type": row[4],
                "location": row[5],
                "position": row[6],
                "experience_min": row[7],
                "experience_max": row[8],
                "education": row[9],
                "tech_stack": row[10],
                "is_data_job": row[11],
                "url": row[12],
                "apply_end_date": row[13],
                "crawled_at": row[14],
                "company_size": row[15],
                "company_name": row[16]
            }
            jobs.append(job_dict)
        
        logger.info(f"SQL query with company info successful. Number of records found: {len(jobs)}")
        return jobs

    except Exception as e:
        logger.error(f"Error in get_job_grid_with_company_info: {e}", exc_info=True)
        return [] # 오류 발생 시 빈 리스트 반환