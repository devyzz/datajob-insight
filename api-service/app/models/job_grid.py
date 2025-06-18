# api-service/app/models/job_grid.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from ..db.session import Base

class JobGrid(Base):
    __tablename__ = "jobposting" 
    
    posting_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer)
    platform_id = Column(Integer)
    title = Column(String(200), nullable=True) 
    job_type = Column(String(50))
    location = Column(String(100))
    position = Column(String(20)) 
    experience_min = Column(String(20))
    experience_max = Column(String(20))
    education = Column(String(20))
    tech_stack = Column(String(100)) 
    is_data_job = Column(Boolean)
    url = Column(String(500))
    apply_end_date = Column(String(10)) 
    crawled_at = Column(DateTime(timezone=False)) 