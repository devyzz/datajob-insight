from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from _common.schema.job_grid import JobGridResponse
from ..db.session import get_db 
from ..crud import crud_job_grid 
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[JobGridResponse])
def get_jobs(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    logger.info(f"api-service진입: get_jobs called with skip={skip}, limit={limit}")
    jobs = crud_job_grid.get_job_grid(db=db, skip=skip, limit=limit) 
    logger.debug(f"Jobs: {jobs}")
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")
    return jobs

@router.get("/stats/overview")
def get_job_stats_overview(db: Session = Depends(get_db)):
    """전체 통계 개요를 반환합니다."""
    logger.info("Getting job stats overview")
    stats = crud_job_grid.get_job_stats_overview(db=db)
    return stats

@router.get("/stats/tech-stack")
def get_tech_stack_stats(db: Session = Depends(get_db)):
    """기술 스택별 통계를 반환합니다."""
    logger.info("Getting tech stack stats")
    stats = crud_job_grid.get_tech_stack_stats(db=db)
    return stats

@router.get("/stats/position")
def get_position_stats(db: Session = Depends(get_db)):
    """포지션별 통계를 반환합니다."""
    logger.info("Getting position stats")
    stats = crud_job_grid.get_position_stats(db=db)
    return stats

@router.get("/stats/company-size")
def get_company_size_stats(db: Session = Depends(get_db)):
    """기업 규모별 통계를 반환합니다."""
    logger.info("Getting company size stats")
    stats = crud_job_grid.get_company_size_stats(db=db)
    return stats

@router.get("/stats/data-jobs")
def get_data_job_stats(db: Session = Depends(get_db)):
    """데이터 직군 통계를 반환합니다."""
    logger.info("Getting data job stats")
    stats = crud_job_grid.get_data_job_stats(db=db)
    return stats

@router.get("/stats/experience")
def get_experience_stats(db: Session = Depends(get_db)):
    """경력별 통계를 반환합니다."""
    logger.info("Getting experience stats")
    stats = crud_job_grid.get_experience_stats(db=db)
    return stats

@router.get("/stats/location")
def get_location_stats(db: Session = Depends(get_db)):
    """지역별 통계를 반환합니다."""
    logger.info("Getting location stats")
    stats = crud_job_grid.get_location_stats(db=db)
    return stats

@router.get("/with-company-info")
def get_jobs_with_company_info(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """company 정보가 포함된 job 데이터를 반환합니다."""
    logger.info(f"api-service진입: get_jobs_with_company_info called with skip={skip}, limit={limit}")
    jobs = crud_job_grid.get_job_grid_with_company_info(db=db, skip=skip, limit=limit) 
    logger.debug(f"Jobs with company info: {jobs}")
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")
    return jobs