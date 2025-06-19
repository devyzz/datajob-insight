from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum

# # MongoDB 설정
# # MONGO_ROOT_USERNAME=admin #인자로
# # MONGO_ROOT_PASSWORD=admin123 #인자로
# CRAWLER_SERVICE_MONGODB_URI="mongodb://mongodb:27017/"
# # 로그 설정
# LOG_LEVEL=INFO


# # 크롤링 설정 (선택사항)
CRAWL_DAYS_BACK=1

# # 기존 URL 조회 기간 (일)
# CRAWL_DAYS_BACK = 1 

class CrawlMethod(Enum):
    REQUESTS = "requests"
    PLAYWRIGHT = "playwright"
    WANTED_API = "wanted_api"

@dataclass
class SiteConfig:
    name: str
    base_url: str
    job_selector: str
    max_pages: int
    delay: float
    crawl_method: CrawlMethod = CrawlMethod.REQUESTS
    search_params: Optional[Dict[str, str]] = None
    detail_click_selector: Optional[str] = None  # 상세페이지 진입용 셀렉터
    playwright_options: Optional[Dict[str, any]] = None
    requests_options: Optional[Dict[str, any]] = None
    # 공통 헤더 추가
    common_headers: Optional[Dict[str, str]] = None
    
    def build_page_url(self, page: int) -> str:
        """페이지별 URL 생성"""
        if self.search_params:
            params = self.search_params.copy()
            for key, value in params.items():
                if isinstance(value, str) and '{page}' in value:
                    params[key] = value.format(page=page)
            
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            return f"{self.base_url}?{param_string}"
        
        return self.base_url

# 공통 헤더 설정
COMMON_BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

# 3개 사이트 설정
SITE_CONFIGS = {
    'wanted': SiteConfig(
        name='wanted',
        base_url='https://www.wanted.co.kr/wdlist/518?country=kr&job_sort=job.latest_order&years=-1&locations=all',
        job_selector='a[data-position-id]',
        detail_click_selector='button[data-cy="job-card"]',  # 카드 클릭용
        max_pages=10,
        delay=2.0,
        crawl_method=CrawlMethod.WANTED_API,
        common_headers=COMMON_BROWSER_HEADERS,
        playwright_options={
            'headless': True,
            'viewport': {'width': 960, 'height': 640},
            'user_agent': COMMON_BROWSER_HEADERS['User-Agent']
        },
        requests_options={
            'headers': {
                **COMMON_BROWSER_HEADERS,
                'Referer': 'https://www.wanted.co.kr/wdlist/518?country=kr&job_sort=job.latest_order&years=-1&locations=all',
                'X-Requested-With': 'XMLHttpRequest'
            }
        }
    ),
    'saramin': SiteConfig(
        name='saramin',
        base_url='https://www.saramin.co.kr/zf_user/jobs/list/job-category',  # 올바른 카테고리 URL
        job_selector='.item_recruit .job_tit a',
        max_pages=1,  # 사람인은 안전하게 3페이지로 제한
        delay=3.0,  # 사람인은 더 긴 딜레이 필요
        crawl_method=CrawlMethod.REQUESTS,
        common_headers={
            **COMMON_BROWSER_HEADERS,
            'Referer': 'https://www.saramin.co.kr/',  # 사람인 메인에서 온 것처럼
        },
        requests_options={
            'headers': {
                **COMMON_BROWSER_HEADERS,
                'Referer': 'https://www.saramin.co.kr/',
            }
        },
        # 기본 검색 파라미터는 크롤러에서 직접 관리 (더 유연함)
        search_params=None,
        playwright_options={
            'headless': True,
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': COMMON_BROWSER_HEADERS['User-Agent']
        }
    ),
    'jobkorea': SiteConfig(
        name='jobkorea',
        base_url='https://www.jobkorea.co.kr/recruit/joblist',
        job_selector='.recruit-info a.title',
        max_pages=10,
        delay=2.0,
        crawl_method=CrawlMethod.REQUESTS,
        common_headers=COMMON_BROWSER_HEADERS,
        search_params={
            'menucode': '2',
            'jobkind': '1',
            'Page_No': '{page}'
        },
        playwright_options={
            'headless': True,
            'viewport': {'width': 960, 'height': 640},
            'user_agent': COMMON_BROWSER_HEADERS['User-Agent']
        }
    )
}