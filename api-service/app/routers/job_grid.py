from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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