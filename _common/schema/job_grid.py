from pydantic import BaseModel
from datetime import datetime 

# API 응답에 대한 Pydantic 모델 정의
class JobGridResponse(BaseModel):
    posting_id: int
    company_id: int
    platform_id: int  # Assuming 'Key' corresponds to '플랫폼 ID'
    title: str
    job_type: str
    location: str
    position: str  # Assuming 'Field' corresponds to '포지션'
    experience_min: str # Assuming 'Field2' corresponds to '경력_min'
    experience_max: str # Assuming 'Field5' corresponds to '경력_max'
    education: str # Assuming 'Field3' corresponds to '학력'
    tech_stack: str # Assuming 'Field4' corresponds to '기술스택'
    is_data_job: bool # Assuming 'Field6' corresponds to '데이터 구분'
    url: str
    apply_end_date: str
    crawled_at: datetime
    
    class Config:
        from_attributes = True
    