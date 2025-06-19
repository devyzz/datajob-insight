import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep
import random

from crawler.base_crawler import JobCrawler
from models.data_models import JobPostingModel
from utils.position_normalizer import normalize_position_data
from config.site_configs import SITE_CONFIGS, COMMON_BROWSER_HEADERS


class JobkoreaCrawler(JobCrawler):
    """
    잡코리아 전용 크롤러
    
    특징:
    - Playwright 기반 JavaScript 렌더링 필요
    - 복잡한 카테고리 필터링 시스템
    - 페이지네이션 처리
    - URL과 메타데이터를 함께 수집하여 상세 페이지에서 활용
    
    주의사항:
    - 사이트 구조 변경에 매우 취약함
    - 클래스명과 셀렉터가 자주 변경됨
    - 안정적인 크롤링을 위해서는 지속적인 모니터링 필요
    """
    
    def __init__(self, site_name: str):
        super().__init__(site_name)
        # URL별 메타데이터 저장소 (해체된 구조로 저장)
        self.url_metadata = {}
    
    def _get_job_urls(self, config, full_crawl: bool = False) -> list:
        """
        잡코리아 URL 수집 - 카테고리 분할 처리로 최대 20개 제한 우회
        
        문제: 잡코리아는 카테고리 선택을 최대 20개까지만 허용
        해결: 카테고리를 17개씩 나누어서 여러 번 검색 실행
        """
        all_job_urls = []
        
        # 카테고리를 17개씩 분할 (최대 20개 제한 고려하여 여유분 확보)
        wanted_categories = [
            "백엔드개발자", "프론트엔드개발자", "웹개발자", "앱개발자", 
            "시스템엔지니어", "네트워크엔지니어", "DBA", "데이터엔지니어", 
            "데이터사이언티스트", "보안엔지니어", "소프트웨어개발자", 
            "게임개발자", "하드웨어개발자", "AI/ML엔지니어", "블록체인개발자",
            "클라우드엔지니어", "웹퍼블리셔", "IT컨설팅", "QA", 
            "AI/ML연구원", "데이터분석가", "데이터라벨러", "프롬프트엔지니어",
            "AI보안전문가", "MLOps엔지니어", "AI서비스개발자"
        ]
        
        # 17개씩 청크로 분할
        chunk_size = 17
        category_chunks = [wanted_categories[i:i + chunk_size] 
                          for i in range(0, len(wanted_categories), chunk_size)]
        
        self.logger.info(f"📊 카테고리 {len(category_chunks)}개 그룹으로 분할 처리")
        
        # Playwright 초기화
        self._init_playwright(config)
        context = self.browser.new_context(
            viewport=config.playwright_options.get('viewport'),
            user_agent=config.playwright_options.get('user_agent')
        )
        
        try:
            for chunk_idx, category_chunk in enumerate(category_chunks, 1):
                self.logger.info(f"🎯 카테고리 그룹 {chunk_idx}/{len(category_chunks)} 처리 중...")
                
                page = context.new_page()
                
                try:
                    # 검색 페이지 접속
                    search_url = "https://www.jobkorea.co.kr/recruit/joblist?menucode=duty"
                    page.goto(search_url, wait_until='networkidle', timeout=60000)
                    page.wait_for_timeout(3000)
                    
                    # 현재 청크의 카테고리들 선택
                    selected_categories = self._select_dev_categories_chunk(page, category_chunk)
                    
                    if not selected_categories:
                        self.logger.warning(f"⚠️ 그룹 {chunk_idx} 카테고리 선택 실패")
                        continue
                    
                    # 검색 실행
                    if not self._execute_search(page):
                        self.logger.warning(f"⚠️ 그룹 {chunk_idx} 검색 실행 실패")
                        continue
                    
                    # URL 수집
                    chunk_urls = self._collect_urls_with_pagination(page, config, full_crawl)
                    all_job_urls.extend(chunk_urls)
                    
                    self.logger.info(f"✅ 그룹 {chunk_idx}: {len(chunk_urls)}개 URL 수집")
                    
                finally:
                    page.close()
                    
        finally:
            context.close()
        
        # 중복 제거
        unique_urls = list(set(all_job_urls))
        self.logger.debug(f"🎯 잡코리아 전체 URL 수집 완료: {len(unique_urls)}개 고유 URL")
        
        return unique_urls

    def _select_dev_categories_chunk(self, page, category_chunk):
        """특정 카테고리 청크만 선택 - 20개 제한 우회용"""
        selected_categories = []
        
        try:
            self.logger.info(f"🎯 카테고리 청크 선택 시작 ({len(category_chunk)}개)")
            
            # 1단계: 메인 카테고리 클릭 (AI·개발·데이터)
            main_category_selectors = [
                'label[for="duty_step1_10031"]',
                '#duty_step1_10031',
                'input[value="10031"]',
            ]
            
            main_category_clicked = False
            for selector in main_category_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        element.click(force=True)
                        page.wait_for_timeout(2000)
                        main_category_clicked = True
                        self.logger.info("✅ AI·개발·데이터 메인 카테고리 클릭 성공")
                        break
                except:
                    continue
            
            if not main_category_clicked:
                self.logger.warning("⚠️ AI·개발·데이터 메인 카테고리 클릭 실패")
                return []
            
            # 2단계: dev-sub 섹션에서 해당 청크의 카테고리만 선택
            dev_sub_section = page.query_selector('div.nano-content.dev-sub')
            if not dev_sub_section:
                self.logger.error("❌ dev-sub 섹션을 찾을 수 없음")
                return []
            
            checkboxes = dev_sub_section.query_selector_all('input[type="checkbox"]')
            self.logger.info(f"📋 {len(checkboxes)}개 체크박스 발견")
            
            # 현재 청크의 카테고리만 선택
            selected_count = 0
            for checkbox in checkboxes:
                try:
                    data_name = checkbox.get_attribute('data-name')
                    
                    if data_name and data_name in category_chunk:
                        if not checkbox.is_checked():
                            page.evaluate('(element) => element.click()', checkbox)
                            page.wait_for_timeout(50)
                        
                        selected_categories.append(data_name)
                        selected_count += 1
                        self.logger.debug(f"✅ 선택: {data_name}")
                        
                except Exception:
                    continue
            
            self.logger.info(f"🎯 청크에서 총 {selected_count}개 카테고리 선택 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 카테고리 청크 선택 중 오류: {e}")
        
        return selected_categories

    def _execute_search(self, page):
        """검색 버튼 클릭하여 필터 적용"""
        try:
            self.logger.debug("🔍 검색 실행 중...")
            
            # 다양한 검색 버튼 셀렉터 시도
            search_selectors = [
                'button:has-text("선택된 조건 검색하기")',
                'input[value*="선택된 조건 검색하기"]',
                'button:has-text("검색하기")',
                '.btn-search'
            ]
            
            for selector in search_selectors:
                try:
                    button = page.query_selector(selector)
                    if button and button.is_visible():
                        button.click()
                        page.wait_for_timeout(5000)  # 필터링 결과 로딩 대기
                        self.logger.info("✅ 검색 버튼 클릭 성공")
                        return True
                except:
                    continue
            
            self.logger.warning("⚠️ 검색 버튼을 찾을 수 없음")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 검색 실행 중 오류: {e}")
            return False

    def _collect_urls_with_pagination(self, page, config, full_crawl):
        """페이지네이션을 통한 URL 수집"""
        job_urls = []
        
        try:
            self.logger.info("🔍 필터링된 결과에서 URL 수집 시작")
            
            max_pages = 10 if full_crawl else config.max_pages  # 테스트용 제한
            consecutive_empty = 0
            
            for page_num in range(1, max_pages + 1):
                try:
                    self.logger.info(f"📄 잡코리아 page {page_num} 처리 중...")
                    
                    # 현재 페이지에서 URL 추출 + metadata 저장
                    page_urls = self._extract_urls_from_current_page(page)
                    
                    if not page_urls:
                        consecutive_empty += 1
                        self.logger.info(f"📄 빈 페이지 ({consecutive_empty}/3)")
                        
                        if consecutive_empty >= 3:
                            self.logger.info("🛑 연속 빈 페이지로 인한 수집 종료")
                            break
                    else:
                        consecutive_empty = 0
                        job_urls.extend(page_urls)
                        self.logger.info(f"📄 page {page_num}: {len(page_urls)}개 URL 수집")
                    
                    # 다음 페이지로 이동
                    if page_num < max_pages:
                        if not self._go_to_next_page(page, page_num + 1):
                            self.logger.info("🛑 다음 페이지 이동 실패")
                            break
                    
                except Exception as e:
                    self.logger.error(f"❌ 페이지 {page_num} 처리 중 오류: {e}")
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
            
        except Exception as e:
            self.logger.error(f"❌ URL 수집 중 오류: {e}")
        
        return job_urls

    def _extract_urls_from_current_page(self, page):
        """현재 페이지에서 채용공고 URL들과 메타데이터를 함께 추출"""
        job_urls = []
        
        try:
            # 잡코리아 채용공고 링크 패턴 - 전체 tr 요소 선택
            job_rows = page.query_selector_all('#dev-gi-list tr.devloopArea')
            self.logger.debug(f"🔍 일반 채용공고 영역에서 {len(job_rows)}개 공고 발견")
            
            for row in job_rows:
                try:
                    # URL 추출
                    link = row.query_selector('td.tplTit strong a[href*="/Recruit/GI_Read/"]')
                    if not link:
                        continue
                    
                    # 회사 정보 URL 추출
                    company_link = row.query_selector('td.tplCo a[href*="/Recruit/Co_Read/"]')
                    company_info_url = ''
                    if company_link:
                        company_info_url = company_link.get_attribute('href')
                        company_info_url = f"https://www.jobkorea.co.kr{company_info_url}"
                        
                    href = link.get_attribute('href')
                    if href:
                        # 절대 경로로 변환
                        if href.startswith('/'):
                            full_url = f"https://www.jobkorea.co.kr{href}"
                        else:
                            full_url = href
                        
                        job_urls.append(full_url)
                        
                        # 메타데이터 추출 및 해체해서 저장
                        metadata = self._extract_metadata_from_row(row, company_info_url)
                        self.url_metadata[full_url] = metadata
                        
                        # 로깅
                        company = metadata.get('company_name', 'Unknown')
                        title = metadata.get('title', 'Unknown')
                        self.logger.info(f"✅ [FOUND] 채용공고 | 회사: {company} | {title} | URL: {full_url}")
                        
                except Exception:
                    continue
            
        except Exception as e:
            self.logger.error(f"❌ URL 추출 중 오류: {e}")
        
        return job_urls

    def _extract_metadata_from_row(self, row, company_info_url: str) -> dict:
        """목록 페이지의 각 row에서 메타데이터 추출 (해체된 구조)"""
        metadata = {
            'title': '',
            'company_name': '',
            'company_info_url': company_info_url,
            'position_description': '',
            'position_list': [],
            'location': '',
            'experience_raw': '',
            'experience_min_years': 0,
            'experience_max_years': 100,
            'education': '',
            'work_type': '',
            'position_level': ''
        }
        
        try:
            # 제목 추출
            title_element = row.query_selector('td.tplTit strong a')
            if title_element:
                metadata['title'] = title_element.get_attribute('title')
            
            # 회사명 추출
            company_element = row.query_selector('td.tplCo a')
            if company_element:
                metadata['company_name'] = company_element.text_content().strip()
            
            # 기타 정보 추출 (etc 클래스)
            etc_elements = row.query_selector_all('td.tplTit p.etc span.cell')
            fields = ['experience_raw', 'education', 'location', 'work_type', 'position_level']
            values = [e.text_content().strip() for e in etc_elements]
            
            for i, field in enumerate(fields):
                if i < len(values):
                    if field == 'experience_raw':
                        metadata[field] = values[i]
                        # 경력 정보 파싱하여 min/max도 저장
                        exp_parsed = self._parse_experience(values[i])
                        metadata['experience_min_years'] = exp_parsed['min_years']
                        metadata['experience_max_years'] = exp_parsed['max_years']
                    else:
                        metadata[field] = values[i]
                
            # 포지션 설명 추출 (.dsc 클래스 - 핵심!)
            dsc_element = row.query_selector('td.tplTit p.dsc')
            if dsc_element:
                dsc_text = dsc_element.text_content().strip()
                metadata['position_description'] = dsc_text
                # 쉼표로 구분하여 리스트 생성
                position_list = [pos.strip() for pos in dsc_text.split(',') if pos.strip()]
                metadata['position_list'] = position_list
                
        except Exception as e:
            self.logger.debug(f"메타데이터 추출 중 오류: {e}")
        
        return metadata

    def _go_to_next_page(self, page, next_page_num):
        """다음 페이지로 이동"""
        try:
            # 앵커 기반 페이지 이동 (#anchorGICnt_N)
            next_anchor = f"#anchorGICnt_{next_page_num}"
            current_url = page.url.split('#')[0]
            next_url = f"{current_url}{next_anchor}"
            
            self.logger.debug(f"🔗 다음 페이지로 이동: page {next_page_num}")
            page.goto(next_url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            sleep(random.uniform(1, 2))
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 페이지 {next_page_num} 이동 실패: {e}")
            return False

    def _crawl_job_detail(self, url: str, config) -> JobPostingModel:
        """
        잡코리아 개별 채용공고 크롤링 - BeautifulSoup 기반 HTML 파싱
        """
        try:
            # URL에서 채용공고 ID 추출
            job_id_match = re.search(r'/GI_Read/(\d+)', url)
            if not job_id_match:
                self.logger.error(f"❌ 잡코리아 URL에서 job_id 추출 실패: {url}")
                return None
            
            job_id = job_id_match.group(1)
            self.logger.info(f"🔍 잡코리아 상세 크롤링 시작: job_id={job_id}")
            
            # HTTP 요청으로 페이지 가져오기
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            }
            sleep(random.uniform(1, 2))
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"❌ 잡코리아 HTTP 오류: {response.status_code}")
                return None
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # JobPostingModel 생성을 위한 데이터 추출
            job_posting = self._parse_jobkorea_detail_to_jobposting(soup, url, job_id)
            
            sleep(random.uniform(1, 2))
            return job_posting
            
        except Exception as e:
            self.logger.error(f"❌ 잡코리아 크롤링 오류 {url}: {e}")
            return None

    def _parse_jobkorea_detail_to_jobposting(self, soup: BeautifulSoup, url: str, job_id: str) -> JobPostingModel:
        """
        잡코리아 상세 페이지 종합 파싱 - wanted 순서에 맞춰 정리
        """
        
        # ================== 기본 식별 정보 ==================
        year = datetime.now().year
        full_job_id = f"jobkorea_{year}_{job_id}"
        platform = "jobkorea"
        job_url = url
        
        # URL 메타데이터에서 기본 정보 가져오기
        metadata = self.url_metadata.get(url, {})
        
        # ================== 플랫폼 및 회사 정보 ==================
        job_title = self._extract_job_title(metadata, soup)
        company_name = self._extract_company_name(metadata, soup)
        company = self._extract_company_info(soup, company_name, metadata.get('company_info_url', ''))
        
        # ================== 공고 기본 정보 ==================
        work_type = self._extract_work_type(metadata, soup)
        location = self._extract_location_info(metadata, soup)
        
        # ================== 자격 요건 ==================
        education = self._extract_education(metadata, soup)
        experience = self._extract_experience_info(metadata, soup)
        
        # ================== 포지션 정보 ==================
        position = self._extract_position_info(metadata, soup)
        
        # ================== 기술 스택 정보 ==================
        tech_stack = self._extract_tech_stack(soup)
        
        # ================== 우대 경험/사항 ==================
        preferred_experience = self._extract_preferred_experience(soup)
        
        # JobPostingModel 생성
        job_posting = JobPostingModel.create(
            job_id=full_job_id,
            job_url=job_url,
            platform=platform,
            job_title=job_title,
            company={
                "name": company_name,
                "size": company.get('size', ''),
                "description": company.get('description', ''),
                "sales": company.get('sales', ''),
                "industry": company.get('industry', '')
            },
            location=location,
            position=position,
            tech_stack=tech_stack,
            experience=experience,
            education=education,
            work_type=work_type,
            preferred_experience=preferred_experience
        )
        
        return job_posting

    # ================== 데이터 추출 메서드들 ==================
    
    def _extract_job_title(self, metadata: dict, soup: BeautifulSoup) -> str:
        """직무 제목 추출"""
        # 메타데이터에서 우선 추출
        if metadata.get('title'):
            return metadata.get('title')
        
        # soup에서 추출 (fallback)
        try:
            title_element = soup.select_one('div.sumTit h3.hd_3')
            if title_element:
                title_text = title_element.get_text(strip=True)
                lines = title_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not any(x in line for x in ['관심기업', '기업인증']):
                        import html
                        return html.unescape(line)
        except Exception:
            pass
        
        return ""
    
    def _extract_company_name(self, metadata: dict, soup: BeautifulSoup) -> str:
        """회사명 추출"""
        # 메타데이터에서 우선 추출
        if metadata.get('company_name'):
            return metadata.get('company_name')
        
        # soup에서 추출 (fallback)
        try:
            selectors = [
                'span.coName',
                'div.view-subtitle.dev-wrap-subtitle a.subtitle-corp'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        except Exception:
            pass
        
        return ""
    
    def _extract_work_type(self, metadata: dict, soup: BeautifulSoup) -> str:
        """근무형태 추출"""
        # 메타데이터에서 우선 추출
        if metadata.get('work_type'):
            return metadata.get('work_type')
        
        # soup에서 추출 (fallback)
        return self._extract_from_work_conditions_section(soup, '고용형태')
    
    def _extract_location_info(self, metadata: dict, soup: BeautifulSoup) -> dict:
        """위치 정보 추출"""
        location_text = metadata.get('location', '')
        
        # soup에서 추가 정보 확인
        if not location_text:
            location_text = self._extract_from_work_conditions_section(soup, '지역')
        
        return self._normalize_location(location_text)
    
    def _extract_education(self, metadata: dict, soup: BeautifulSoup) -> str:
        """학력 정보 추출"""
        # 메타데이터에서 우선 추출
        if metadata.get('education'):
            return metadata.get('education')
        
        # soup에서 추출 (fallback)
        return self._extract_from_qualifications_section(soup, '학력')
    
    def _extract_experience_info(self, metadata: dict, soup: BeautifulSoup) -> dict:
        """경력 정보 추출"""
        # 메타데이터에서 우선 추출
        if metadata.get('experience_raw'):
            return {
                "raw_text": metadata.get('experience_raw'),
                "min_years": metadata.get('experience_min_years', 0),
                "max_years": metadata.get('experience_max_years', 100)
            }
        
        # soup에서 추출 (fallback)
        exp_text = self._extract_from_qualifications_section(soup, '경력')
        return self._parse_experience(exp_text)
    
    def _extract_position_info(self, metadata: dict, soup: BeautifulSoup) -> dict:
        """포지션 정보 추출 - pageviewObj.dimension44에서 파싱"""
        try:
            # JavaScript에서 pageviewObj.dimension44 값 추출
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if script.string and 'pageviewObj.dimension44' in script.string:
                    # 정규표현식으로 dimension44 값 추출
                    pattern = r'pageviewObj\.dimension44\s*=\s*[\'"]([^\'"]*)[\'"]'
                    match = re.search(pattern, script.string)
                    
                    if match:
                        positions_string = match.group(1)
                        position_list = [pos.strip() for pos in positions_string.split('|') if pos.strip()]
                        
                        position_raw = {
                            "raw_text": positions_string.replace('|', ', '),
                            "raw_list": position_list
                        }
                        
                        # 정규화 적용
                        return normalize_position_data(
                            position_raw["raw_text"], 
                            position_raw["raw_list"]
                        )
            
            # fallback: 기존 metadata 방식
            position_raw = {
                "raw_text": metadata.get('position_description', ''),
                "raw_list": metadata.get('position_list', [])
            }
            
            return normalize_position_data(
                position_raw["raw_text"], 
                position_raw["raw_list"]
            )
            
        except Exception as e:
            self.logger.debug(f"포지션 정보 추출 오류: {e}")
            return {"raw_text": "", "raw_list": [], "normalized": []}

    def _extract_tech_stack(self, soup: BeautifulSoup) -> dict:
        """기술 스택 정보 추출"""
        tech_stack = {"raw_text": "", "raw_list": []}
        
        try:
            # 1. 옛날 스타일 박스에서 추출
            qualifications_section = soup.select_one('div.tbRow.clear div.tbCol dl.tbList')
            if qualifications_section:
                tech_text = self._extract_from_dt_dd_section(qualifications_section, '스킬')
                if tech_text:
                    tech_stack['raw_text'] = tech_text
                    tech_stack['raw_list'] = [tech.strip() for tech in tech_text.split(',') if tech.strip()]
                    return tech_stack
                    
            # 2. 세련된 스타일 스킬 태그에서 추출
            tech_stack_section = soup.select_one('ul.view-content-detail-skill')
            if tech_stack_section:
                tech_items = tech_stack_section.find_all('li')
                tech_stack['raw_list'] = [item.get_text(strip=True) for item in tech_items]
                tech_stack['raw_text'] = ', '.join(tech_stack['raw_list'])
                        
        except Exception as e:
            self.logger.debug(f"기술 스택 추출 오류: {e}")
        
        return tech_stack

    def _extract_preferred_experience(self, soup: BeautifulSoup) -> dict:
        """우대사항 추출"""
        preferred = {"raw_text": "", "raw_list": []}
        
        try:
            preferred_section = soup.select_one('dl.tbAdd.tbPref')
            if preferred_section:
                dd_element = preferred_section.select_one('dd')
                if dd_element:
                    preferred_text = dd_element.get_text(strip=True)
                    preferred['raw_text'] = preferred_text
                    preferred_list = [item.strip() for item in preferred_text.split(',') if item.strip()]
                    preferred['raw_list'] = preferred_list
                    
        except Exception as e:
            self.logger.debug(f"우대사항 추출 오류: {e}")
        
        return preferred

    def _extract_company_info(self, soup: BeautifulSoup, company_name: str, company_info_url: str) -> dict:
        """회사 정보 추출"""
        company = {
            "name": company_name,
            "size": "", #대기업/중견/중소
            "description": "",
            "sales": "",
            "industry": ""
        }
        
        try:
            # 1. 현재 페이지의 기업정보 테이블에서 추출
            self._extract_from_legacy_section(soup, company)
            
            # 2. 필수 정보가 부족하면 추가 페이지에서 보완
            if not self._has_essential_company_info(company) and company_info_url:
                self._extract_from_company_page(company_info_url, company)
                
            # 3. 아 여기서도 안된다? 회사 정보 페이지가 https://www.jobkorea.co.kr/company/1810241 들어가보면 기업정보로 한번 더 들어가야하는 구조 이경우에는 company_info_url끝에다가 "?tabType=l"을 추가한다
            if not self._has_essential_company_info(company) and company_info_url:
                self._extract_from_company_page(company_info_url + "?tabType=l", company)
            return company
            
        except Exception as e:
            self.logger.debug(f"회사 정보 추출 오류: {e}")
            return company

    # ================== 헬퍼 메서드들 ==================
    
    def _extract_from_qualifications_section(self, soup: BeautifulSoup, field_name: str) -> str:
        """지원자격 섹션에서 특정 필드 추출"""
        try:
            qualifications_section = soup.select_one('div.tbRow.clear div.tbCol dl.tbList')
            if qualifications_section:
                return self._extract_from_dt_dd_section(qualifications_section, field_name)
        except Exception:
            pass
        return ""
    
    def _extract_from_work_conditions_section(self, soup: BeautifulSoup, field_name: str) -> str:
        """근무조건 섹션에서 특정 필드 추출"""
        try:
            work_sections = soup.select('div.tbRow.clear div.tbCol')
            if len(work_sections) > 1:
                work_section = work_sections[1]
                work_list = work_section.select_one('dl.tbList')
                if work_list:
                    return self._extract_from_dt_dd_section(work_list, field_name)
        except Exception:
            pass
        return ""
    
    def _extract_from_dt_dd_section(self, section, field_name: str) -> str:
        """dt/dd 구조에서 특정 필드 추출"""
        try:
            dt_elements = section.find_all('dt')
            dd_elements = section.find_all('dd')
            
            for dt, dd in zip(dt_elements, dd_elements):
                if dt.get_text(strip=True) == field_name:
                    return dd.get_text(strip=True)
        except Exception:
            pass
        return ""
    
    def _extract_from_legacy_section(self, soup: BeautifulSoup, company: dict):
        """기업정보 테이블에서 정보 추출"""
        try:
            # # 현재 페이지의 기업정보 테이블
            # company_info_section = soup.select_one('table.table-basic-infomation-primary')
            # if company_info_section:
            #     self._extract_from_table(company_info_section, company)
            #     return
                
            # 옛날 스타일 dt/dd 구조
            legacy_section = soup.select_one('div.tbCol.coInfo dl.tbList')
            if legacy_section:
                field_mapping = {
                    '산업': 'industry',
                    '사원수': 'size', 
                    '매출액': 'sales',
                    '기업형태': 'description',
                    '설립': 'description'
                }
                #self.logger.debug(f"🔍 기업정보 테이블 추출: {legacy_section}")
                
                for field_ko, field_en in field_mapping.items():
                    value = self._extract_from_dt_dd_section(legacy_section, field_ko)
                    if value:
                        if field_en == 'description' and company[field_en]:
                            company[field_en] += f", {value}"
                        else:
                            company[field_en] = value

        except Exception:
            pass
    
    def _has_essential_company_info(self, company: dict) -> bool:
        """필수 정보 확인"""
        return bool(company['size'] or company['sales'] or company['industry'])
    
    def _extract_from_company_page(self, company_info_url: str, company: dict):
        """회사 정보 페이지에서 추가 정보 추출"""
        try:
            headers = COMMON_BROWSER_HEADERS
            sleep(random.uniform(1, 2))
            response = self.session.get(company_info_url, headers=headers, timeout=30)
            self.logger.debug(f"🔍 회사 페이지 요청: {company_info_url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 회사명 추출 (기존에 없을 경우)
                if not company.get('name'):
                    company_name = self._extract_company_name_from_jobkorea(soup)
                    if company_name:
                        company['name'] = company_name
                        self.logger.debug(f"✅ 회사명 발견: {company_name}")
                
                # 메인 정보 테이블 찾기
                company_info_section = soup.select_one('table.table-basic-infomation-primary')
                
                if company_info_section:
                    self.logger.debug("✅ 회사 페이지에서 테이블 발견")
                    self._extract_from_table(company_info_section, company)
                else:
                    # 다른 테이블 선택자 시도
                    alternative_selectors = [
                        '.basic-infomation-container table',
                        '.company-infomation-container table'
                    ]
                    for selector in alternative_selectors:
                        table = soup.select_one(selector)
                        if table:
                            self.logger.debug(f"✅ 대체 테이블 발견: {selector}")
                            self._extract_from_table(table, company)
                            break
                
                # 추가 정보 추출
                self._extract_additional_jobkorea_info(soup, company)
                        
        except Exception as e:
            self.logger.debug(f"회사 페이지 요청 오류: {e}")

    def _extract_company_name_from_jobkorea(self, soup):
        """잡코리아에서 회사명 추출"""
        name_selectors = [
            '.company-header-branding-body .name',
            '.name',
            'title'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name and '잡코리아' not in name:
                    # 제목에서 회사명만 추출
                    if selector == 'title':
                        parts = name.split(' ')
                        if len(parts) > 0:
                            name = parts[0]  # 첫 번째 부분이 회사명
                    return name
        return None

    def _extract_additional_jobkorea_info(self, soup, company):
        """잡코리아에서 추가 정보 추출"""
        try:
            # 업종 정보 (헤더에서)
            if not company.get('industry'):
                summary_item = soup.select_one('.summary-item')
                if summary_item:
                    industry = summary_item.get_text(strip=True)
                    if industry:
                        company['industry'] = industry
                        self.logger.debug(f"✅ 헤더에서 업종 발견: {industry}")
            
            # 기업소개
            if not company.get('description_long'):
                intro_element = soup.select_one('.introduce-body')
                if intro_element:
                    intro_text = intro_element.get_text(strip=True)
                    if intro_text and len(intro_text) > 10:
                        company['description_long'] = intro_text
                        self.logger.info(f"✅ 기업소개 발견: {intro_text[:100]}...")
                        
        except Exception as e:
            self.logger.debug(f"추가 정보 추출 오류: {e}")

    def _extract_from_table(self, table_element, company: dict):
        """테이블 구조에서 회사 정보 추출 (잡코리아 최적화)"""
        try:
            fields = table_element.select('tr.field')
            if not fields:
                fields = table_element.find_all('tr', class_='field')
            
            for field in fields:
                labels = field.find_all('th', class_='field-label')
                values = field.find_all('td', class_='field-value')
                
                for label, value in zip(labels, values):
                    label_text = label.get_text(strip=True)
                    
                    # 값 추출 - 여러 패턴 시도
                    value_text = None
                    
                    # 패턴 1: div.value
                    value_element = value.select_one('div.value')
                    if value_element:
                        value_text = value_element.get_text(strip=True)
                    
                    # 패턴 2: div.values div.value  
                    if not value_text:
                        value_element = value.select_one('div.values div.value')
                        if value_element:
                            value_text = value_element.get_text(strip=True)
                    
                    # 패턴 3: 링크가 있는 경우 (홈페이지)
                    if not value_text:
                        link_element = value.select_one('div.value a')
                        if link_element:
                            value_text = link_element.get_text(strip=True)
                    
                    if value_text:
                        # 확장된 필드 매핑
                        field_mapping = {
                            '산업': 'industry',
                            '기업구분': 'size', #대기업/중견/중소
                            '사원수': 'description',
                            '매출액': 'sales', 
                            '설립일': 'founded',
                            '자본금': 'capital',
                            '대표자': 'ceo',
                            '주요사업': 'business',
                            '4대보험': 'insurance',
                            '홈페이지': 'website',
                            '주소': 'location'
                        }
                        
                        field_key = field_mapping.get(label_text)
                        if field_key and not company.get(field_key):
                            company[field_key] = value_text
                            self.logger.debug(f"✅ 매핑 성공: {label_text} → {field_key}: {value_text}")
                            
        except Exception as e:
            self.logger.debug(f"테이블 정보 추출 오류: {e}")