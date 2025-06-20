import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep
from playwright.sync_api import sync_playwright

from crawler.base_crawler import JobCrawler
from models.data_models import JobPostingModel
from utils.position_normalizer import normalize_position_data
from config.site_configs import SITE_CONFIGS, COMMON_BROWSER_HEADERS

class WantedCrawler(JobCrawler):
    """원티드 전용 크롤러"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._playwright = None
        self._browser = None
        self._context = None
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        super().__enter__()
        self._init_playwright()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self._cleanup_playwright()
        super().__exit__(exc_type, exc_val, exc_tb)
    
    def _init_playwright(self):
        """Playwright 초기화 (lazy loading)"""
        try:
            if not self._playwright:
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                self._context = self._browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                self.logger.info("✅ Playwright 브라우저 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ Playwright 초기화 실패: {e}")
            self._playwright = None
    
    def _cleanup_playwright(self):
        """Playwright 리소스 정리"""
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            self.logger.info("✅ Playwright 리소스 정리 완료")
        except Exception as e:
            self.logger.error(f"❌ Playwright 정리 중 오류: {e}")
    
    def _get_job_urls(self, config, full_crawl: bool = False) -> list:
        """
        원티드 API로 URL 수집
        """
        job_urls = []
        
        # 세션 헤더 업데이트
        self.session.headers.update(config.requests_options.get('headers', {}))
        
        # 전체 크롤링이면 충분히 큰 페이지 수, 아니면 설정값 사용
        max_pages = 100000 if full_crawl else config.max_pages
        consecutive_empty = 0  # 연속으로 빈 응답 카운트
        
        # 개발전체 - 채용공고 조회 API
        successful_api = {
                'name' : 'v1_chaos', 
                'url' : 'https://www.wanted.co.kr/api/chaos/navigation/v1/results',
                'params_template' : {
                    'country' : 'kr',
                    'job_sort' : 'job.latest_order',
                    'years' : -1,
                    'locations' : 'all',
                    'limit' : 20, 
                    'job_group_id' : 518
                }
            }
        
        for page in range(0, max_pages):
            try:
                params = {**successful_api['params_template'], 'offset': page * 20}
                response = self.session.get(successful_api['url'], params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get('data', [])
                else:
                    self.logger.warning(f"❌ {successful_api['name']} 실패: {response.status_code}")
                    continue
                
                self.logger.info(f"🔗 원티드 API 호출 중 (page {page + 1}, API: {successful_api['name'] if successful_api else 'Unknown'})...")
                
                if not jobs:
                    consecutive_empty += 1
                    self.logger.info(f"📄 빈 응답 ({consecutive_empty}/3)")
                    
                    # 연속 3번 빈 응답이면 종료
                    if consecutive_empty >= 3:
                        self.logger.info("🛑 더 이상 채용공고가 없어서 종료")
                        break
                    continue
                else:
                    consecutive_empty = 0  # 데이터가 있으면 리셋
                
                for job in jobs:
                    job_url = f"https://www.wanted.co.kr/wd/{job.get('id')}"
                    if job_url:
                        job_urls.append(job_url)
                        
                        self.logger.info(f"✅ [FOUND] 채용공고 | 회사: {job.get('company', {}).get('name', 'Unknown')} | 포지션: {job.get('position') or job.get('title', 'Unknown')} | URL: {job_url}")
                
                time.sleep(config.delay)
                
            except Exception as e:
                self.logger.error(f"❌ 원티드 page {page} 오류: {e}")
                
        return list(set(job_urls))
    
    def _crawl_job_detail(self, url: str, config) -> JobPostingModel:
        """
        원티드 상세 페이지 크롤링 - API + HTML 파싱 방식
        """
        
        # URL에서 job_id 추출
        job_id_match = re.search(r'/wd/(\d+)', url)
        if not job_id_match:
            self.logger.error(f"❌ 원티드 URL에서 job_id 추출 실패: {url}")
            return None
        
        job_id = job_id_match.group(1)
        self.logger.info(f"🔍 원티드 상세 크롤링 시작: url={url} | job_id={job_id}")
        
        try:
            # API로 상세 정보 가져오기
            detail_data = self._fetch_wanted_detail_api(job_id)
            if not detail_data:
                self.logger.error(f"❌ 원티드 상세 API 호출 실패: job_id={job_id}")
                return None
            
            # 회사 페이지에서 추가 정보 가져오기 (매출 정보 포함)
            company_info = self._fetch_wanted_company_info(detail_data)
            
            # 모든 정보를 detail_data에 통합
            detail_data = self._append_company_info_to_detail_data(detail_data, company_info)
            
            # JobPostingModel로 파싱
            job_posting = self._parse_wanted_detail_to_jobposting(detail_data, url)
            sleep(config.delay)
            
            return job_posting
            
        except Exception as e:
            self.logger.error(f"❌ 원티드 크롤링 오류 {url}: {e}")
            return None

    def _fetch_wanted_detail_api(self, job_id: str) -> dict:
        """
        원티드 상세 정보 API 호출
        """
        try:
            # API URL 구성
            timestamp = int(time.time() * 1000)
            detail_url = f"https://www.wanted.co.kr/api/chaos/jobs/v4/{job_id}/details"
            
            # config에서 헤더 가져오기
            config = self.session.headers.copy()
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'https://www.wanted.co.kr/wd/{job_id}',
                'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'X-Requested-With': 'XMLHttpRequest'
            }
            headers.update(config)
            
            # API 호출 실행
            response = self.session.get(
                detail_url, 
                headers=headers,
                params={str(timestamp): ''},
                timeout=30
            )
            
            # 응답 상태 검증
            if response.status_code == 200:
                data = response.json()
                
                if data.get('message') == 'ok' and data.get('data'):
                    return data['data']
                else:
                    self.logger.warning(f"⚠️ 원티드 API 응답 구조 오류: {data.get('message', 'Unknown')}")
                    return None
            else:
                self.logger.warning(f"⚠️ 원티드 API HTTP 오류: {response.status_code} for job_id={job_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 원티드 상세 API 호출 중 예외 발생: {e}")
            return None

    def _fetch_wanted_company_info(self, detail_data: dict) -> dict:
        """
        원티드 회사 정보 페이지 크롤링 - BeautifulSoup 사용
        """
        
        try:
            # 회사 ID 추출
            job_data = detail_data.get('job', {})
            company_data = job_data.get('company', {})
            company_id = company_data.get('id')
            
            if not company_id:
                self.logger.info("⚠️ 회사 ID가 없어서 회사 정보 페이지 크롤링 스킵")
                return {}
            
            # 원티드 회사 정보 페이지 URL 구성
            company_url = f"https://www.wanted.co.kr/company/{company_id}"
            
            self.logger.debug(f"🔍 회사 정보 크롤링: {company_data.get('name')} | {company_url}")
            
            # config에서 헤더 가져오기
            
            headers = COMMON_BROWSER_HEADERS
            
            # 회사 페이지 요청
            response = self.session.get(company_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                self.logger.info(f"⚠️ 회사 정보 페이지 HTTP 오류: {response.status_code}")
                return {}
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # CompanyInfoTable에서 정보 추출
            company_info = self._parse_company_info_table(soup, company_url)
            
            if company_info:
                self.logger.debug(f"✅ 회사 정보 추출 성공: {len(company_info)}개 항목")
                return company_info
            else:
                self.logger.info("⚠️ 회사 정보 테이블을 찾을 수 없음")
                return {}
                
        except Exception as e:
            self.logger.info(f"회사 정보 페이지 크롤링 실패 (선택적 기능): {e}")
            return {}

    def _parse_company_info_table(self, soup, company_url: str) -> dict:
        """회사 정보 테이블에서 정보 추출 - 매출 정보 포함"""

        company_info = {}

        try:
            # 1. 기존 CompanyInfoTable에서 표준산업분류 추출
            company_info_div = soup.select_one('div[class^="CompanyInfoTable_wrapper"]')
            if company_info_div:
                self.logger.debug("✅ CompanyInfoTable_wrapper 섹션 발견")
                
                definition_lists = company_info_div.find_all('dl', class_=lambda x: x and 'CompanyInfoTable_definition' in x)

                for dl in definition_lists:
                    try:
                        dt_element = dl.find('dt', class_=lambda x: x and 'CompanyInfoTable_definition__dt' in x)
                        dd_element = dl.find('dd', class_=lambda x: x and 'CompanyInfoTable_definition__dd' in x)

                        if not dt_element or not dd_element:
                            continue

                        key = dt_element.get_text(strip=True)
                        
                        # 표준산업분류
                        if key == '표준산업분류':
                            value = dd_element.get_text(strip=True)
                            if value and value != '-':
                                company_info['industry_classification'] = value
                                self.logger.debug(f"✅ 표준산업분류: {value}")

                        # 기존 매출액 (참고용)
                        elif key == '매출액':
                            value = self._extract_revenue_value(dd_element)
                            if value and value != '-':
                                company_info['old_revenue'] = value
                                self.logger.debug(f"ℹ️ 기존 매출액: {value}")

                    except Exception as e:
                        self.logger.debug(f"❌ 항목 처리 중 오류 발생: {e}")
                        continue

            # 2. 매출 차트에서 최신 매출 정보 추출 (우선순위 높음) - Playwright 사용
            sales_info = self._extract_sales_from_chart(company_url)
            if sales_info:
                company_info['revenue'] = sales_info
                self.logger.debug(f"✅ 최신 매출 정보 추출: {sales_info}")
            elif company_info.get('old_revenue'):
                # 차트에서 찾지 못했으면 기존 매출액 사용
                company_info['revenue'] = company_info['old_revenue']
                self.logger.debug(f"📋 기존 매출액 사용: {company_info['old_revenue']}")

            return company_info

        except Exception as e:
            self.logger.error(f"❌ 회사 정보 파싱 오류: {e}")
            return {}
        
    def _extract_sales_from_chart(self, company_url: str) -> str:
        """
        Playwright를 사용하여 동적 차트에서 매출 정보 추출
        """
        try:
            # Playwright가 초기화되지 않았다면 초기화
            if not self._playwright:
                self._init_playwright()
            
            if not self._context:
                self.logger.error("❌ Playwright 컨텍스트가 없음")
                return ""
            
            # 새 페이지 생성
            page = self._context.new_page()
            
            try:
                self.logger.debug(f"🌐 Playwright로 페이지 로드 중: {company_url}")
                
                # 페이지 로드
                page.goto(company_url, wait_until='domcontentloaded', timeout=30000)
                
                # 차트가 로드될 때까지 잠시 대기
                page.wait_for_timeout(2000)
                
                # 방법 1: ChartSummary + wds 클래스 방식
                self.logger.debug("🔍 방법 1: SalesChart + wds 클래스 방식")
                chart_wrapper = page.query_selector('div[class*="SalesChart_wrapper"]')
                if chart_wrapper:
                    self.logger.debug("✅ SalesChart_wrapper 발견")
                    
                    # wds 클래스를 가진 모든 요소 찾기
                    wds_elements = chart_wrapper.query_selector_all('div[class*="wds"]')
                    self.logger.debug(f"📋 wds 요소 수: {len(wds_elements)}")
                    
                    for i, element in enumerate(wds_elements):
                        text = element.text_content().strip()
                        self.logger.debug(f"  wds 요소 {i+1}: '{text}'")
                        
                        # 숫자와 "원"이 포함된 것 찾기 (매출 라벨 제외)
                        if (any(char.isdigit() for char in text) and 
                            any(unit in text for unit in ['만원', '억원', '천원', '원']) and
                            '매출' not in text):
                            self.logger.debug(f"✅ 방법1 성공! 차트에서 매출값 추출: {text}")
                            return text
                    
                    self.logger.debug("❌ 방법1 실패: 적합한 wds 요소 없음")
                else:
                    self.logger.debug("❌ 방법1 실패: ChartSummary_wrapper 없음")
                
                # 방법 2: 매출 라벨 기반 검색
                self.logger.debug("🔍 방법 2: 매출 라벨 기반 검색")
                
                # 매출이 포함된 텍스트를 가진 요소 찾기
                sales_elements = page.query_selector_all('text=매출')
                sales_elements.extend(page.query_selector_all('[text*="매출"]'))
                
                for sales_element in sales_elements:
                    try:
                        self.logger.debug(f"✅ 매출 라벨 발견: '{sales_element.text_content().strip()}'")
                        
                        # 부모 컨테이너에서 형제 요소들 찾기
                        parent = sales_element.locator('..')
                        if parent:
                            # 형제 요소들에서 숫자+원 패턴 찾기
                            siblings = parent.query_selector_all('div, span')
                            
                            for sibling in siblings:
                                text = sibling.text_content().strip()
                                if text and text != sales_element.text_content().strip():
                                    self.logger.debug(f"  형제 요소: '{text}'")
                                    
                                    if (any(char.isdigit() for char in text) and 
                                        any(unit in text for unit in ['만원', '억원', '천원', '원'])):
                                        self.logger.info(f"✅ 방법2 성공! 라벨 기반 매출값 추출: {text}")
                                        return text
                    except Exception as e:
                        self.logger.debug(f"❌ 매출 라벨 처리 중 오류: {e}")
                        continue
                
                self.logger.debug("❌ 모든 방법 실패: 차트에서 매출 정보를 찾을 수 없음")
                return ""
                
            finally:
                page.close()
                
        except Exception as e:
            self.logger.error(f"❌ Playwright 매출 차트 파싱 오류: {e}")
            return ""

    def _extract_revenue_value(self, dd_element) -> str:
        """매출액 값 추출 - trailing text 처리"""
        try:
            # trailing text 요소들 찾기
            trailing_texts = dd_element.find_all('div', class_=lambda x: x and 'trailingText' in x)
            
            if trailing_texts:
                # trailing text 제거한 메인 텍스트
                dd_copy = dd_element.__copy__()
                for trailing in dd_copy.find_all('div', class_=lambda x: x and 'trailingText' in x):
                    trailing.decompose()
                main_text = dd_copy.get_text(strip=True)
                
                # trailing text 수집
                trailing_values = [t.get_text(strip=True) for t in trailing_texts]
                
                # 결합 (예: "25억 3,353만" + "원" = "25억 3,353만원")
                if main_text and trailing_values:
                    return main_text + ''.join(trailing_values)
            
            # 기본 텍스트
            return dd_element.get_text(strip=True)
            
        except Exception:
            return dd_element.get_text(strip=True) if dd_element else ""

    def _append_company_info_to_detail_data(self, detail_data: dict, company_info: dict) -> dict:
        """회사 정보를 detail_data에 통합"""
        
        if not company_info:
            return detail_data
        
        try:
            # 구조 보장
            if 'job' not in detail_data:
                detail_data['job'] = {}
            if 'company' not in detail_data['job']:
                detail_data['job']['company'] = {}
            
            company_section = detail_data['job']['company']
            
            # 표준산업분류 추가 (기존 industry_name이 없는 경우만)
            if company_info.get('industry_classification'):
                if not company_section.get('industry_name'):
                    company_section['industry_name'] = company_info['industry_classification']
                    self.logger.debug(f"✅ 표준산업분류 추가: {company_info['industry_classification']}")
            
            # 매출액 정보 추가 (회사 페이지의 최신 정보 우선)
            if company_info.get('revenue'):
                company_section['revenue'] = company_info['revenue']
                company_section['sales'] = company_info['revenue']  # 호환성을 위해 둘 다 설정
                self.logger.debug(f"✅ 회사 페이지에서 매출액 정보 추가: {company_info['revenue']}")
            
            return detail_data
            
        except Exception as e:
            self.logger.error(f"❌ 회사 정보 통합 오류: {e}")
            return detail_data

    def _parse_wanted_detail_to_jobposting(self, detail_data: dict, url: str) -> JobPostingModel:
        """
        원티드 API 데이터를 JobPostingModel로 변환
        """
        
        # API 응답 구조에서 필요한 데이터 추출
        job_data = detail_data.get('job', {})
        job_detail = job_data.get('detail', {})
        company_data = job_data.get('company', {})
        address_data = job_data.get('address', {})
        
        # ================== 기본 식별 정보 ==================
        year = datetime.now().year
        job_id = f"wanted_{year}_{job_data.get('id', '')}"
        job_url = url
        platform = "wanted"
        
        # ================== 플랫폼 및 회사 정보 ==================
        job_title = job_detail.get('position', '')
        company = {
            "name": company_data.get('name', ''),
            "size": self._infer_company_size_from_tags(job_data.get('attraction_tags', [])),
            "description": job_detail.get('intro', ''),
            "sales": company_data.get('revenue', ''),
            "industry": company_data.get('industry_name', ''),
            "founded": self._infer_company_founded_date_from_tags(job_data.get('attraction_tags', [])),
        }
        
        # ================== 공고 기본 정보 ==================
        work_type = self._map_employment_type(job_data.get('employment_type', ''))
        location = {
            "city": address_data.get('location', ''),
            "district": address_data.get('district', ''),
            "detail_address": address_data.get('full_location', '')
        }
        
        # ================== 자격 요건 ==================
        requirements_text = job_detail.get('requirements', '')
        #self.logger.debug(f"🔍 자격 요건: {requirements_text}")
        education = self._extract_education_from_text(requirements_text)
        experience = self._map_experience_years(job_data)
        
        # ================== 포지션 정보 ==================
        position_raw = self._extract_position_from_api(job_data.get('category_tag', {}))
        position = normalize_position_data(
            position_raw["raw_text"], 
            position_raw["raw_list"]
        )
        
        # ================== 기술 스택 정보 ==================
        tech_stack = self._extract_tech_stack_from_api(job_data.get('skill_tags', []), job_detail)
        
        # ================== 우대 경험/사항 ==================
        preferred_experience = self._extract_preferred_experience_from_api(job_detail)
        
        # JobPostingModel 생성 및 반환
        job = JobPostingModel.create(
            job_id=job_id,
            job_url=job_url,
            platform=platform,
            job_title=job_title,
            company=company,
            location=location,
            position=position,
            tech_stack=tech_stack,
            experience=experience,
            education=education,
            work_type=work_type,
            preferred_experience=preferred_experience
        )
        
        return job

    # ================== 데이터 추출 헬퍼 메서드들 ==================
    
    def _extract_position_from_api(self, category_tag: dict) -> dict:
        """API에서 포지션 원시 데이터 추출"""
        position_texts = []
        
        # parent_tag 처리
        parent_tag = category_tag.get('parent_tag', {})
        if parent_tag.get('text'):
            position_texts.append(parent_tag.get('text'))
        
        # child_tags 처리
        child_tags = category_tag.get('child_tags', [])
        for tag in child_tags:
            if isinstance(tag, dict) and tag.get('text'):
                tag_text = tag.get('text')
                if tag_text not in position_texts:
                    position_texts.append(tag_text)
        
        return {
            "raw_text": ', '.join(position_texts) if position_texts else '',
            "raw_list": position_texts
        }
    
    def _extract_tech_stack_from_api(self, skill_tags: list, job_detail: dict) -> dict:
        """API에서 기술스택 원시 데이터 추출"""
        tech_names = []
        
        # skill_tags에서 기술명 추출
        for tag in skill_tags:
            if isinstance(tag, dict) and tag.get('text'):
                tech_name = tag.get('text')
                if tech_name not in tech_names:
                    tech_names.append(tech_name)
        
        # 추가 기술스택을 job_detail에서 보완 추출
        main_tasks = job_detail.get('main_tasks', '')
        requirements = job_detail.get('requirements', '')
        preferred_points = job_detail.get('preferred_points', '')
        additional_techs = self._extract_techs_from_text(main_tasks + ' ' + requirements + ' ' + preferred_points)
        
        # 중복 제거하며 합치기 (skill_tags 우선순위)
        all_techs = tech_names.copy()
        for tech in additional_techs:
            if tech and tech not in all_techs:
                all_techs.append(tech)
        
        return {
            "raw_text": ', '.join(all_techs) if all_techs else '',
            "raw_list": all_techs
        }

    def _extract_preferred_experience_from_api(self, job_detail: dict) -> dict:
        """API에서 우대사항 원시 데이터 추출"""
        preferred_text = job_detail.get('preferred_points', '')
        
        if not preferred_text:
            return {"raw_text": "", "raw_list": []}
        
        # 문단 단위로 분리 시도
        separators = [r'•\s*', r'\*\s*', r'-\s*', r'\d+\.\s*', r'\n\s*', r';\s*']
        
        raw_list = [preferred_text]  # 기본값
        
        for sep_pattern in separators:
            parts = re.split(sep_pattern, preferred_text)
            if len(parts) > 1:
                raw_list = [part.strip() for part in parts if part.strip() and len(part.strip()) >= 5]
                break
        
        if not raw_list:
            raw_list = [preferred_text] if preferred_text else []
        
        return {
            "raw_text": preferred_text,
            "raw_list": raw_list
        }

    def _infer_company_size_from_tags(self, attraction_tags: list) -> str:
        """어트랙션 태그에서 회사 규모 추론"""
        size_tag_mapping = {
            10402: "50명이하",  # 스타트업
            10403: "51-100명",
            10404: "101-500명", 
            10405: "501-1000명",
            10406: "1000명이상"
        }
        
        for tag in attraction_tags:
            if isinstance(tag, dict):
                tag_id = tag.get('tag_type_id')
            else:
                tag_id = tag
                
            if tag_id in size_tag_mapping:
                return size_tag_mapping[tag_id]
        
        return ""

    def _infer_company_founded_date_from_tags(self, attraction_tags: list) -> str:
        """어트랙션 태그에서 회사 설립 연차 추론"""
        founded_tag_mapping = {
            10407: "설립3년이하",   # 추정 (10408 이전)
            10408: "설립4~9년", 
            10409: "설립10년이상",
        }
        
        for tag in attraction_tags:
            if isinstance(tag, dict):
                tag_id = tag.get('tag_type_id')
            else:
                tag_id = tag
                
            if tag_id in founded_tag_mapping:
                return founded_tag_mapping[tag_id]
        
        return ""

    def _map_employment_type(self, employment_type: str) -> str:
        """원티드 고용형태를 표준 형태로 매핑"""
        mapping = {
            'regular': '정규직',
            'contract': '계약직',
            'intern': '인턴',
            'freelance': '프리랜서',
            'part_time': '파트타임'
        }
        
        return mapping.get(employment_type, employment_type)

    def _map_experience_years(self, job_data: dict) -> dict:
        """경력 년수 매핑"""
        annual_to = job_data.get('annual_to', 0)
        annual_from = job_data.get('annual_from', 0)
        is_newbie = job_data.get('is_newbie', False)
        
        if is_newbie:
            return {
                "raw_text": "신입",
                "min_years": 0,
                "max_years": 1
            }
        else:
            raw_text = f"경력{annual_from}-{annual_to}년" if annual_to < 100 else f"경력{annual_from}년 이상"
            
            return {
                "raw_text": raw_text,
                "min_years": annual_from,
                "max_years": annual_to 
            }