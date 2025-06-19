from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib

@dataclass
class JobPostingModel:
    """
    정형화된 채용공고 데이터 모델
    크롤링된 원시 데이터를 구조화된 형태로 저장
    """
    # ================== 기본 식별 정보 ==================
    job_id: str # 플랫폼별 고유 공고 ID (플랫폼명_년도_번호)
    job_url: str # 플랫폼별 공고 URL
    platform: str # 플랫폼명
    job_title: str # 공고 제목

    # ================== 플랫폼 및 회사 정보 ==================
    company: Dict[str, Any]  # {name, size, description, sales, industry}

    # ================== 공고 기본 정보 ==================
    work_type: Optional[str] = None  # 정규직/계약직/인턴/프리랜서/파트타임
    location: Dict[str, Any] = None  # {city, district, detail_address}

    # ================== 자격 요건 ==================
    education: Optional[str] = None  # 무관/고졸/전문대졸/대졸/석사이상
    experience: Dict[str, Any] = None  # {min_years, max_years, description}

    # ================== 포지션 정보 ==================
    position: Dict[str, Any] = None  # {raw_text, raw_list, normalized}

    # ================== 기술 스택 정보 ==================
    tech_stack: Dict[str, Any] = None  # {raw_text, raw_list}

    # ================== 우대 경험/사항 ==================
    preferred_experience: Dict[str, Any] = None  # {raw_text, raw_list}

    # ================== 크롤링 메타데이터 ==================
    crawled_at: datetime = None # 크롤링 일시

    # ================== 기타 ==================
    #_id: Optional[Any] = None # MongoDB ObjectId

    def to_dict(self) -> dict:
        """MongoDB에 저장할 딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def create(cls, job_id: str, job_url: str, platform: str, job_title: str = "", **kwargs):
        """팩토리 메서드로 생성 - 기본값 자동 설정"""
        
        # 기본값 설정
        defaults = {
            'company': kwargs.get('company', {}),
            'location': kwargs.get('location', {}),
            'experience': kwargs.get('experience', {}),
            'position': kwargs.get('position', {}),
            'tech_stack': kwargs.get('tech_stack', {}),
            'preferred_experience': kwargs.get('preferred_experience', {}),
            'crawled_at': kwargs.get('crawled_at', datetime.now())
        }
        
        # kwargs에서 기본값들 업데이트
        for key, default_value in defaults.items():
            if key not in kwargs:
                kwargs[key] = default_value
        
        return cls(
            job_id=job_id,
            job_url=job_url,
            platform=platform,
            job_title=job_title,
            **kwargs
        )