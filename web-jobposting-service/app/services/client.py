import httpx # httpx는 비동기 통신을 지원. requests 보다 빠름
from typing import List, Dict
from ..core.config import settings # 설정 가져오기

async def get_job_postings_from_api(skip: int = 0, limit: int = 100) -> List[Dict]: # 함수 이름 및 파라미터 변경
    print("get_job_posting_from_api함수진입")
    endpoint = f"{settings.API_SERVICE_BASE_URL}/api/" 
    async with httpx.AsyncClient() as client_session:
        try:
            response = await client_session.get(endpoint, params={"skip": skip, "limit": limit})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"API 요청 실패 (HTTP 상태 코드: {e.response.status_code}): {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"API 연결 실패: {e}")
            return []
        
