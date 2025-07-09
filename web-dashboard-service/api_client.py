import httpx
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from config import settings
from _common.schema.job_grid import JobGridResponse, CompanyResponse

class APIClient:
    def __init__(self):
        self.base_url = settings.API_SERVICE_BASE_URL
        self.api_url = f"{self.base_url}/api"
    
    async def get_jobs(self, skip: int = 0, limit: int = 100) -> List[JobGridResponse]:
        """API에서 채용 정보를 가져옵니다. (타입 안전성 보장)"""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.api_url, params={"skip": skip, "limit": limit})
                response.raise_for_status()
                data = response.json()
                # JobGridResponse 스키마를 사용하여 타입 안전성 보장
                return [JobGridResponse(**job) for job in data]
        except Exception as e:
            st.error(f"API 요청 실패: {e}")
            return []
    
    async def get_jobs_with_company_info(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """company 정보가 포함된 채용 정보를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/with-company-info", params={"skip": skip, "limit": limit})
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"Company 정보 포함 API 요청 실패: {e}")
            return []
    
    async def get_stats_overview(self) -> Dict[str, Any]:
        """전체 통계 개요를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/stats/overview")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"통계 개요 API 요청 실패: {e}")
            return {}
    
    async def get_tech_stack_stats(self) -> List[Dict[str, Any]]:
        """기술 스택 통계를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/stats/tech-stack")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"기술 스택 통계 API 요청 실패: {e}")
            return []
    
    async def get_position_stats(self) -> List[Dict[str, Any]]:
        """포지션 통계를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/stats/position")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"포지션 통계 API 요청 실패: {e}")
            return []
    
    async def get_company_size_stats(self) -> List[Dict[str, Any]]:
        """기업 규모 통계를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/stats/company-size")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"기업 규모 통계 API 요청 실패: {e}")
            return []
    
    async def get_data_job_stats(self) -> List[Dict[str, Any]]:
        """데이터 직군 통계를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/stats/data-jobs")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"데이터 직군 통계 API 요청 실패: {e}")
            return []
    
    async def get_experience_stats(self) -> List[Dict[str, Any]]:
        """경력별 통계를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/stats/experience")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"경력별 통계 API 요청 실패: {e}")
            return []
    
    async def get_location_stats(self) -> List[Dict[str, Any]]:
        """지역별 통계를 가져옵니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"{self.api_url}/stats/location")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"지역별 통계 API 요청 실패: {e}")
            return []

# 동기 함수들 (Streamlit에서 사용하기 위해)
def get_jobs_sync(skip: int = 0, limit: int = 100) -> List[JobGridResponse]:
    """동기적으로 채용 정보를 가져옵니다. (타입 안전성 보장)"""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_jobs(skip, limit))

def get_jobs_with_company_info_sync(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """동기적으로 company 정보가 포함된 채용 정보를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_jobs_with_company_info(skip, limit))

def get_stats_overview_sync() -> Dict[str, Any]:
    """동기적으로 통계 개요를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_stats_overview())

def get_tech_stack_stats_sync() -> List[Dict[str, Any]]:
    """동기적으로 기술 스택 통계를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_tech_stack_stats())

def get_position_stats_sync() -> List[Dict[str, Any]]:
    """동기적으로 포지션 통계를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_position_stats())

def get_company_size_stats_sync() -> List[Dict[str, Any]]:
    """동기적으로 기업 규모 통계를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_company_size_stats())

def get_data_job_stats_sync() -> List[Dict[str, Any]]:
    """동기적으로 데이터 직군 통계를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_data_job_stats())

def get_experience_stats_sync() -> List[Dict[str, Any]]:
    """동기적으로 경력별 통계를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_experience_stats())

def get_location_stats_sync() -> List[Dict[str, Any]]:
    """동기적으로 지역별 통계를 가져옵니다."""
    import asyncio
    client = APIClient()
    return asyncio.run(client.get_location_stats())

@st.cache_data(ttl=3600)
def load_data_from_api():
    """API에서 데이터를 로드하고 DataFrame으로 변환합니다."""
    jobs = get_jobs_sync()
    if jobs:
        # JobGridResponse 객체들을 딕셔너리로 변환
        jobs_dict = [job.dict() for job in jobs]
        df = pd.DataFrame(jobs_dict)
        
        # location에서 구 정보 추출 (Python에서 처리)
        if not df.empty and 'location' in df.columns:
            df['location_district'] = df['location'].apply(
                lambda x: x.split(' ')[1] if x and ' ' in x else x
            )
        
        # experience_min을 숫자로 변환
        df['experience_min_years'] = df['experience_min'].apply(
            lambda x: 0 if x == '신입' else 
            int(''.join(filter(str.isdigit, x))) if x and '년' in x else 0
        )
        
        return df
    return pd.DataFrame() 