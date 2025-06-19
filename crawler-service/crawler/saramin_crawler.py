import time
import re
import random
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from crawler.base_crawler import JobCrawler
from models.data_models import JobPostingModel
from utils.position_normalizer import normalize_position_data

class SaraminCrawler(JobCrawler):
    """
    봇 탐지 회피를 위한 최적화된 사람인 크롤러
    """
    
    def __init__(self, site_name: str):
        super().__init__(site_name)
        self.url_metadata = {}
        self.playwright = None
        self.browser = None
        self.browser_context = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def __enter__(self):
        """스텔스 모드 브라우저 초기화"""
        try:
            self.playwright = sync_playwright().start()
            
            # 봇 탐지 회피를 위한 고급 설정
            self.browser = self.playwright.chromium.launch(
                headless=False,  # headless를 False로 변경 (탐지 회피)
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # 이미지 로딩 비활성화로 속도 향상
                    '--disable-javascript',  # JS 비활성화 옵션 (필요시)
                    '--user-agent=' + random.choice(self.user_agents),
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-popup-blocking',
                    '--disable-translate',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            # 스텔스 컨텍스트 생성
            self.browser_context = self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 720, 'height': 480},  # 일반적인 해상도
                locale='ko-KR',
                timezone_id='Asia/Seoul',
                permissions=['geolocation'],
                geolocation={'latitude': 37.5665, 'longitude': 126.9780},  # 서울 좌표
                color_scheme='light',
                reduced_motion='no-preference',
                forced_colors='none',
                # 추가 스텔스 설정
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            # 봇 탐지 스크립트 차단
            self._inject_stealth_scripts()
            
            return self
            
        except Exception as e:
            self.logger.error(f"❌ 브라우저 초기화 실패: {e}")
            self._cleanup_browser()
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """안전한 브라우저 정리"""
        self._cleanup_browser()
    
    def _cleanup_browser(self):
        """브라우저 리소스 정리"""
        try:
            if self.browser_context:
                # 모든 페이지 먼저 닫기
                for page in self.browser_context.pages:
                    try:
                        page.close()
                    except:
                        pass
                time.sleep(0.5)
                self.browser_context.close()
                self.browser_context = None
                
            if self.browser:
                time.sleep(0.5)
                self.browser.close()
                self.browser = None
                
            if self.playwright:
                time.sleep(0.5)
                self.playwright.stop()
                self.playwright = None
                
            self.logger.debug("✅ 브라우저 리소스 정리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 브라우저 정리 중 오류: {e}")
    
    def _inject_stealth_scripts(self):
        """봇 탐지 회피 스크립트 주입"""
        try:
            # WebDriver 속성 숨기기
            stealth_script = """
            // WebDriver 속성 제거
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Chrome 속성 추가
            window.chrome = {
                runtime: {},
            };
            
            // Permissions API 모킹
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Plugin array 모킹
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Languages 설정
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en'],
            });
            """
            
            # 모든 페이지에 스크립트 주입
            self.browser_context.add_init_script(stealth_script)
            
        except Exception as e:
            self.logger.error(f"❌ 스텔스 스크립트 주입 실패: {e}")
    
    def _load_page_with_playwright(self, url: str, max_retries: int = 3) -> str:
        """재시도 로직이 포함된 안전한 페이지 로드"""
        for attempt in range(max_retries):
            try:
                # 페이지 생성
                page = self.browser_context.new_page()
                
                # 불필요한 리소스 차단으로 속도 향상
                page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
                
                self.logger.debug(f"🌐 페이지 로딩 시도 {attempt + 1}/{max_retries}: {url}")
                
                # 랜덤 딜레이 (봇 탐지 회피)
                if attempt > 0:
                    delay = random.uniform(2.0, 5.0)
                    self.logger.debug(f"⏳ 재시도 전 대기: {delay:.1f}초")
                    time.sleep(delay)
                
                # 페이지 로드
                response = page.goto(
                    url, 
                    wait_until='domcontentloaded',  # networkidle 대신 더 빠른 옵션
                    timeout=20000  # 타임아웃 단축
                )
                
                # 응답 상태 확인
                if response and response.status >= 400:
                    self.logger.warning(f"⚠️ HTTP {response.status} 응답: {url}")
                    if response.status == 403:
                        self.logger.error("🚫 403 Forbidden - 봇 탐지됨")
                        page.close()
                        # 더 긴 대기 후 재시도
                        time.sleep(random.uniform(10.0, 15.0))
                        continue
                
                # 페이지 완전 로딩 대기
                try:
                    # 핵심 요소가 로드될 때까지 대기
                    page.wait_for_selector('body', timeout=10000)
                    
                    # 추가 대기 (동적 콘텐츠 로딩)
                    random_wait = random.uniform(1.5, 3.0)
                    page.wait_for_timeout(int(random_wait * 1000))
                    
                except PlaywrightTimeoutError:
                    self.logger.warning("⚠️ 페이지 로딩 타임아웃 - 계속 진행")
                
                # HTML 콘텐츠 추출
                html_content = page.content()
                page.close()
                
                # 성공적으로 콘텐츠를 가져왔는지 확인
                if len(html_content) > 1000:  # 최소 콘텐츠 길이 체크
                    self.logger.debug(f"✅ 페이지 로딩 성공: {len(html_content)} 글자")
                    return html_content
                else:
                    self.logger.warning(f"⚠️ 콘텐츠 부족: {len(html_content)} 글자")
                    
            except PlaywrightTimeoutError:
                self.logger.warning(f"⚠️ 시도 {attempt + 1} 타임아웃: {url}")
                try:
                    page.close()
                except:
                    pass
                    
            except Exception as e:
                self.logger.error(f"❌ 시도 {attempt + 1} 실패: {e}")
                try:
                    page.close()
                except:
                    pass
        
        self.logger.error(f"❌ 모든 재시도 실패: {url}")
        return None
    
    def _load_iframe_content_with_playwright(self, iframe_url: str) -> BeautifulSoup:
        """iframe 전용 최적화된 로딩"""
        try:
            # iframe은 더 관대한 설정으로
            page = self.browser_context.new_page()
            
            # 리소스 차단 (CSS, 이미지 등)
            page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,js}", lambda route: route.abort())
            
            self.logger.debug(f"🖼️ iframe 로딩: {iframe_url}")
            
            # 더 짧은 타임아웃으로 빠르게 처리
            page.goto(iframe_url, wait_until='domcontentloaded', timeout=15000)
            
            # 최소한의 대기
            page.wait_for_timeout(1000)
            
            try:
                # user_content가 있는지 확인
                page.wait_for_selector('div.user_content', timeout=5000)
            except:
                self.logger.debug("⚠️ user_content 로딩 지연")
            
            iframe_html = page.content()
            page.close()
            
            soup = BeautifulSoup(iframe_html, 'html.parser')
            user_content_div = soup.find('div', class_='user_content')
            
            if user_content_div:
                content_text = user_content_div.get_text(strip=True)
                self.logger.debug(f"✅ iframe 콘텐츠: {len(content_text)} 글자")
                return user_content_div
            else:
                self.logger.warning(f"⚠️ user_content 없음: {iframe_url}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ iframe 로딩 실패: {e}")
            try:
                page.close()
            except:
                pass
            return None
    
    def _get_job_urls(self, config, full_crawl: bool = False) -> list:
        """목록 페이지는 기존 requests 방식 유지 (동적 로딩 영향 적음)"""
        all_job_urls = []
        
        base_url = "https://www.saramin.co.kr/zf_user/jobs/list/job-category"
        base_params = {
            'cat_mcls': '2',
            'search_done': 'y',
            'page_count': '50',
            'sort': 'RD',
            'type': 'job-category'
        }
        
        self.session.headers.update(config.common_headers)
        max_pages = 10 if full_crawl else config.max_pages
        consecutive_empty = 0
        
        self.logger.info(f"🎯 사람인 IT 카테고리 크롤링 시작 (최대 {max_pages}페이지)")
        
        try:
            for page_num in range(1, max_pages + 1):
                try:
                    params = base_params.copy()
                    params['page'] = str(page_num)
                    
                    if page_num > 1:
                        sleep(random.uniform(2, 4))
                    
                    response = self.session.get(base_url, params=params, timeout=30) 
                    response.raise_for_status()
                    self.logger.info(f"📄 사람인 page {page_num} 처리 중...")
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_urls = self._extract_urls_from_current_page(soup)
                    
                    if not page_urls:
                        consecutive_empty += 1
                        self.logger.info(f"📄 빈 페이지 ({consecutive_empty}/3)")
                        
                        if consecutive_empty >= 3:
                            self.logger.info("🛑 연속 빈 페이지로 인한 수집 종료")
                            break
                    else:
                        consecutive_empty = 0
                        all_job_urls.extend(page_urls)
                        self.logger.info(f"📄 page {page_num}: {len(page_urls)}개 URL 수집")
                    
                except Exception as e:
                    self.logger.error(f"❌ 페이지 {page_num} 처리 중 오류: {e}")
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        break
        
        except Exception as e:
            self.logger.error(f"❌ 사람인 URL 수집 중 오류: {e}")
        
        unique_urls = list(set(all_job_urls))
        self.logger.info(f"🎯 사람인 전체 URL 수집 완료: {len(unique_urls)}개 고유 URL")
        
        return unique_urls

    def _extract_urls_from_current_page(self, soup: BeautifulSoup) -> list:
        """기존 URL 추출 로직 유지"""
        job_urls = []
        
        try:
            recruiting_section = soup.find('section', class_='list_recruiting')
            if not recruiting_section:
                self.logger.warning("⚠️ list_recruiting 섹션을 찾을 수 없음")
                return []
            
            list_items = recruiting_section.find_all('div', class_='list_item')
            list_items = list_items[:30]
            
            for item in list_items:
                try:
                    job_link = self._extract_job_link_from_item(item)
                    if not job_link:
                        continue
                    
                    href = job_link.get('href')
                    if not href:
                        continue
                    
                    if href.startswith('/'):
                        full_url = f"https://www.saramin.co.kr{href}"
                    else:
                        full_url = href
                    
                    if not self._is_valid_saramin_job_url(full_url):
                        continue
                    
                    job_urls.append(full_url)
                    
                    metadata = self._extract_metadata_from_item(item, full_url)
                    self.url_metadata[full_url] = metadata
                    
                    company = metadata.get('company_name', 'Unknown')
                    title = metadata.get('position_title', 'Unknown')
                    self.logger.info(f"✅ [FOUND] 채용공고 | 회사: {company} | {title}")
                    
                except Exception:
                    continue
            
        except Exception as e:
            self.logger.error(f"❌ URL 추출 중 오류: {e}")
        
        return job_urls

    def _extract_job_link_from_item(self, item):
        """기존 링크 추출 로직 유지"""
        job_tit = item.find('div', class_='job_tit')
        if job_tit:
            job_link = job_tit.find('a', class_='str_tit')
            if job_link:
                return job_link
        
        job_link = item.find('a', href=re.compile(r'/zf_user/jobs/relay/view'))
        if job_link:
            return job_link
        
        job_link = item.find('a', href=re.compile(r'/zf_user/jobs/view'))
        if job_link:
            return job_link
        
        return None

    def _is_valid_saramin_job_url(self, url: str) -> bool:
        """기존 URL 검증 로직 유지"""
        return ('saramin.co.kr' in url and 
                ('jobs/relay/view' in url or 'jobs/view' in url))

    def _extract_metadata_from_item(self, item, job_url: str) -> dict:
        """공고 아이템에서 메타데이터 추출"""
        metadata = {
            'job_url': job_url,
            'company_name': '',
            'position_title': '',
            'location': '',
            'career': '',
            'education': '',
            'deadline': '',
            'registration_date': '',
            'job_sectors': [],
            'badges': [],
            'company_group': '',
            'company_type': '',
            'rec_idx': ''
        }
        
        try:
            # rec_idx 추출 (식별용)
            rec_match = re.search(r'rec_idx[=:](\d+)', job_url)
            if rec_match:
                metadata['rec_idx'] = rec_match.group(1)
            
            # 회사명 추출
            company_elem = item.find('div', class_=lambda x: x and 'company' in x)
            if company_elem:
                company_link = company_elem.find('a')
                if company_link:
                    metadata['company_name'] = company_link.get_text(strip=True)
                else:
                    metadata['company_name'] = company_elem.get_text(strip=True)
            
            # 공고 제목 추출
            title_elem = item.find('div', class_=lambda x: x and ('job' in x or 'title' in x))
            if title_elem:
                title_link = title_elem.find('a')
                if title_link:
                    title_text = (title_link.get('title') or 
                                 title_link.get_text(strip=True))
                    metadata['position_title'] = title_text
            
            # 직무 분야 추출
            self._extract_job_sectors(item, metadata)
            
            # 뱃지 정보 추출
            self._extract_badges(item, metadata)
            
        except Exception as e:
            self.logger.debug(f"메타데이터 추출 중 오류: {e}")
        
        return metadata
        
    def _extract_job_sectors(self, item, metadata):
        """직무 분야 추출"""
        try:
            sector_elements = item.find_all(['span', 'div'], 
                                          class_=lambda x: x and 'sector' in x)
            for elem in sector_elements:
                sectors = [span.get_text(strip=True) for span in elem.find_all('span')]
                metadata['job_sectors'].extend(sectors)
        except Exception:
            pass

    def _extract_badges(self, item, metadata):
        """뱃지 정보 추출"""
        try:
            badge_elements = item.find_all(['span', 'div'], 
                                         class_=lambda x: x and 'badge' in x)
            for elem in badge_elements:
                badges = [span.get_text(strip=True) for span in elem.find_all('span')]
                for badge in badges:
                    if badge and len(badge) < 20:  # 너무 긴 텍스트 제외
                        metadata['badges'].append(badge)
        except Exception:
            pass

    
    def _crawl_job_detail(self, url: str, config) -> JobPostingModel:
        """봇 탐지 회피가 포함된 상세 크롤링"""
        try:
            rec_match = re.search(r'rec_idx[=:](\d+)', url)
            if not rec_match:
                self.logger.error(f"❌ rec_idx 추출 실패: {url}")
                return None
            
            rec_idx = rec_match.group(1)
            self.logger.info(f"🔍 상세 크롤링 시작: rec_idx={rec_idx}")
            
            # 랜덤 딜레이 (봇 탐지 회피)
            delay = random.uniform(1.0, 3.0)
            self.logger.debug(f"⏳ 크롤링 전 대기: {delay:.1f}초")
            time.sleep(delay)
            
            # 안전한 페이지 로딩
            html_content = self._load_page_with_playwright(url)
            if not html_content:
                self.logger.error(f"❌ 페이지 로딩 실패: {url}")
                return None
            
            # 파싱 진행
            soup = BeautifulSoup(html_content, 'html.parser')
            job_section = self._get_job_specific_section(soup, rec_idx)
            
            if not job_section:
                self.logger.error(f"❌ 공고 섹션 없음: {rec_idx}")
                return None
            
            job_posting = self._parse_saramin_detail_to_jobposting(job_section, url, rec_idx)
            
            # 성공 후 추가 딜레이
            success_delay = random.uniform(0.5, 1.5)
            time.sleep(success_delay)
            
            return job_posting
            
        except Exception as e:
            self.logger.error(f"❌ 크롤링 오류 {url}: {e}")
            return None

    def _get_job_specific_section(self, soup: BeautifulSoup, rec_idx: str) -> BeautifulSoup:
        """공고별 고유 섹션 추출"""
        try:
            self.logger.debug(f"🔍 공고별 섹션 탐색 시작: rec_idx={rec_idx}")
            
            all_sections = soup.find_all('section', class_='jview')
            self.logger.debug(f"📋 전체 jview 섹션 수: {len(all_sections)}")
            
            target_class = f"jview-0-{rec_idx}"
            job_section = soup.find('section', class_=lambda x: x and 'jview' in x and target_class in x)
            
            if job_section:
                self.logger.debug(f"✅ 공고 섹션 발견: {job_section.get('class')}")
                return job_section
            
            for section in all_sections:
                class_list = section.get('class', [])
                for class_name in class_list:
                    if rec_idx in class_name and 'jview-' in class_name:
                        self.logger.debug(f"✅ 공고 섹션 발견 (패턴2): {class_list}")
                        return section
            
            self.logger.warning(f"⚠️ 공고별 섹션을 찾을 수 없어 전체 페이지 사용: {rec_idx}")
            return soup
            
        except Exception as e:
            self.logger.error(f"❌ 공고 섹션 추출 오류: {e}")
            return soup

    def _parse_saramin_detail_to_jobposting(self, job_section: BeautifulSoup, url: str, rec_idx: str) -> JobPostingModel:
        """
        사람인 상세 페이지 종합 파싱 - jv_summary 섹션에서 핵심 정보 추출
        """
        # ================== 기본 식별 정보 ==================
        year = datetime.now().year
        full_job_id = f"saramin_{year}_{rec_idx}"
        platform = "saramin"
        job_url = url
        
        # URL 메타데이터에서 기본 정보 가져오기
        metadata = self.url_metadata.get(url, {})
        
        # ================== jv_summary 섹션에서 핵심 정보 추출 ==================
        summary_info = self._extract_summary_info(job_section)
        
        # ================== 플랫폼 및 회사 정보 ==================
        job_title = self._extract_job_title(metadata, job_section)
        company_name = self._extract_company_name(metadata, job_section)
        company = self._extract_company_info(job_section, company_name, metadata)
        
        # ================== 공고 기본 정보 (summary에서 우선 추출) ==================
        work_type = summary_info.get('work_type') or self._extract_work_type(metadata, job_section)
        location = summary_info.get('location') or self._extract_location_info(metadata, job_section)
        
        # ================== 자격 요건 (summary에서 우선 추출) ==================
        education = summary_info.get('education') or self._extract_education(metadata, job_section)
        experience = summary_info.get('experience') or self._extract_experience_info(metadata, job_section)
        
        # ================== 직무 정보 ==================
        position = self._extract_position_info(metadata, job_section)
        
        # ================== 기술 스택 정보 ==================
        tech_stack = self._extract_tech_stack(job_section)
        
        # ================== 우대 경험/사항 ==================
        preferred_experience = self._extract_preferred_experience(job_section)
        
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

    def _extract_summary_info(self, job_section: BeautifulSoup) -> dict:
        """
        jv_summary 섹션에서 핵심 정보 일괄 추출
        """
        summary_info = {
            'work_type': '',
            'location': {},
            'education': '',
            'experience': {}
        }
        
        try:
            # jv_summary 섹션 찾기
            summary_section = job_section.find('div', class_='jv_summary')
            if not summary_section:
                self.logger.debug("⚠️ jv_summary 섹션을 찾을 수 없음")
                return summary_info
            
            # dl/dt/dd 구조에서 정보 추출
            dl_elements = summary_section.find_all('dl')
            
            for dl in dl_elements:
                dt = dl.find('dt')
                dd = dl.find('dd')
                
                if not dt or not dd:
                    continue
                    
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                
                # 경력 정보 추출
                if key == '경력':
                    summary_info['experience'] = self._parse_experience(value)
                    self.logger.debug(f"✅ summary에서 경력 추출: {value}")
                
                # 학력 정보 추출  
                elif key == '학력':
                    summary_info['education'] = value
                    self.logger.debug(f"✅ summary에서 학력 추출: {value}")
                
                # 근무형태 추출
                elif key == '근무형태':
                    summary_info['work_type'] = value
                    self.logger.debug(f"✅ summary에서 근무형태 추출: {value}")
                
                # 근무지역 추출
                elif key == '근무지역':
                    summary_info['location'] = self._normalize_location(value)
                    self.logger.debug(f"✅ summary에서 근무지역 추출: {value}")
                    
        except Exception as e:
            self.logger.error(f"❌ summary 정보 추출 오류: {e}")
        
        return summary_info

    # ================== 기술스택 추출 ==================
    
    def _extract_tech_stack(self, job_section: BeautifulSoup) -> dict:
        """기술스택 추출 - 다단계 fallback 처리"""
        tech_stack = {"raw_text": "", "raw_list": []}
        
        try:
            # 1. 우선 명시적 기술 태그에서 시도
            tech_section = job_section.find('div', class_='job_skill')
            if tech_section:
                tech_items = tech_section.find_all(['span', 'div'], class_='skill')
                tech_list = [item.get_text(strip=True) for item in tech_items if item.get_text(strip=True)]
                
                if tech_list:
                    tech_stack['raw_list'] = tech_list
                    tech_stack['raw_text'] = ', '.join(tech_list)
                    self.logger.debug(f"✅ 명시적 기술 태그에서 추출: {tech_list}")
                    return tech_stack
            
            # 2. iframe 내부 user_content에서 추출 시도
            iframe_techs = self._extract_tech_stack_from_iframe(job_section)
            if iframe_techs['raw_list']:
                self.logger.debug(f"✅ iframe user_content에서 기술스택 추출: {len(iframe_techs['raw_list'])}개")
                return iframe_techs
            
            # 3. iframe 추출 실패시 외부 텍스트에서 fallback 추출
            self.logger.debug("⚠️ iframe 기술스택 추출 실패 - 외부 텍스트에서 fallback 시도")
            
            # 3-1. 전체 jview 섹션에서 추출
            full_text = job_section.get_text()
            extracted_techs = self._extract_techs_from_text(full_text)
            
            if extracted_techs:
                tech_stack['raw_list'] = list(set(extracted_techs))
                tech_stack['raw_text'] = ', '.join(tech_stack['raw_list'])
                self.logger.debug(f"✅ 외부 텍스트에서 기술스택 추출: {len(tech_stack['raw_list'])}개")
                return tech_stack
            
            # 3-2. job_description 클래스에서 시도
            job_content = job_section.find('div', class_='job_description')
            if job_content:
                content_text = job_content.get_text()
                extracted_techs = self._extract_techs_from_text(content_text)
                
                if extracted_techs:
                    tech_stack['raw_list'] = list(set(extracted_techs))
                    tech_stack['raw_text'] = ', '.join(tech_stack['raw_list'])
                    self.logger.debug(f"✅ job_description에서 기술스택 추출: {len(tech_stack['raw_list'])}개")
                    return tech_stack
            
            self.logger.warning("⚠️ 모든 방법으로 기술스택 추출 실패")
                        
        except Exception as e:
            self.logger.error(f"❌ 기술 스택 추출 오류: {e}")
        
        return tech_stack

    def _extract_tech_stack_from_iframe(self, job_section: BeautifulSoup) -> dict:
        """iframe 내부 user_content에서 기술스택 추출"""
        tech_stack = {"raw_text": "", "raw_list": []}
        
        try:
            # iframe 찾기
            iframe_element = job_section.find('iframe', class_='iframe_content')
            if not iframe_element:
                self.logger.debug("⚠️ iframe_content를 찾을 수 없음")
                return tech_stack
            
            iframe_src = iframe_element.get('src')
            if not iframe_src:
                self.logger.debug("⚠️ iframe src가 없음")
                return tech_stack
            
            # iframe URL을 절대 URL로 변환
            if iframe_src.startswith('/'):
                iframe_url = f"https://www.saramin.co.kr{iframe_src}"
            else:
                iframe_url = iframe_src
            
            # Playwright로 iframe 내용 로드
            user_content_soup = self._load_iframe_content_with_playwright(iframe_url)
            if not user_content_soup:
                self.logger.warning(f"⚠️ iframe 내용 로드 실패 - 외부 fallback 시도: {iframe_url}")
                return tech_stack
            
            # user_content 전체 텍스트에서 기술스택 추출
            content_text = user_content_soup.get_text(strip=True)
            
            # 텍스트가 너무 적으면 의미있는 기술스택 추출이 어려움
            if len(content_text) < 30:
                self.logger.warning(f"⚠️ iframe 텍스트 콘텐츠 부족 ({len(content_text)}글자) - 기술스택 추출 포기")
                return tech_stack
            
            extracted_techs = self._extract_techs_from_text(content_text)
            
            if extracted_techs:
                tech_stack['raw_list'] = list(set(extracted_techs))
                tech_stack['raw_text'] = ', '.join(tech_stack['raw_list'])
                self.logger.debug(f"✅ iframe에서 기술스택 추출 완료: {len(tech_stack['raw_list'])}개")
            else:
                self.logger.debug(f"⚠️ iframe에서 기술스택 미발견 - 콘텐츠 길이: {len(content_text)}글자")
            
        except Exception as e:
            self.logger.error(f"❌ iframe 기술스택 추출 오류: {e}")
        
        return tech_stack

    # ================== 우대사항 추출 ==================
    
    def _extract_preferred_experience(self, job_section: BeautifulSoup) -> dict:
        """iframe user_content에서 우대사항 추출 - 동적 로딩 대응"""
        preferred = {"raw_text": "", "raw_list": []}
        
        try:
            # 1. 우선 기존 방식으로 시도
            preferred_section = job_section.find('div', class_='preferred')
            if preferred_section:
                preferred_text = preferred_section.get_text(strip=True)
                if preferred_text:
                    preferred['raw_text'] = preferred_text
                    
                    if '•' in preferred_text:
                        preferred_list = [item.strip() for item in preferred_text.split('•') if item.strip()]
                    elif '-' in preferred_text:
                        preferred_list = [item.strip() for item in preferred_text.split('-') if item.strip()]
                    else:
                        preferred_list = [preferred_text] if preferred_text else []
                    
                    preferred['raw_list'] = preferred_list
                    self.logger.debug(f"✅ 기존 방식으로 우대사항 추출: {len(preferred_list)}개")
                    return preferred
            
            # 2. iframe 내부 user_content에서 추출 시도
            iframe_preferred = self._extract_preferred_experience_from_iframe(job_section)
            if iframe_preferred['raw_text']:
                self.logger.info(f"✅ iframe user_content에서 우대사항 추출: {len(iframe_preferred['raw_list'])}개")
                return iframe_preferred
                    
        except Exception as e:
            self.logger.error(f"❌ 우대사항 추출 오류: {e}")
        
        return preferred

    def _extract_preferred_experience_from_iframe(self, job_section: BeautifulSoup) -> dict:
        """iframe 내부 user_content에서 우대사항 추출"""
        preferred = {"raw_text": "", "raw_list": []}
        
        try:
            # iframe 찾기
            iframe_element = job_section.find('iframe', class_='iframe_content')
            if not iframe_element:
                return preferred
            
            iframe_src = iframe_element.get('src')
            if not iframe_src:
                return preferred
            
            if iframe_src.startswith('/'):
                iframe_url = f"https://www.saramin.co.kr{iframe_src}"
            else:
                iframe_url = iframe_src
            
            # Playwright로 iframe 내용 로드
            user_content_soup = self._load_iframe_content_with_playwright(iframe_url)
            if not user_content_soup:
                self.logger.warning(f"⚠️ iframe 내용 로드 실패 - 우대사항 추출 포기: {iframe_url}")
                return preferred
            
            # 텍스트 콘텐츠 확인
            content_text = user_content_soup.get_text(strip=True)
            if len(content_text) < 30:
                self.logger.warning(f"⚠️ iframe 텍스트 콘텐츠 부족 ({len(content_text)}글자) - 우대사항 추출 포기")
                return preferred
            
            # user_content에서 우대사항 섹션 찾기
            preferred_content = self._extract_preferred_from_job_sections(user_content_soup)
            
            if preferred_content['raw_text']:
                preferred = preferred_content
                self.logger.debug(f"✅ iframe에서 우대사항 추출 완료: {len(preferred['raw_list'])}개")
            else:
                self.logger.debug(f"⚠️ iframe에서 우대사항 미발견 - 콘텐츠 길이: {len(content_text)}글자")
            
        except Exception as e:
            self.logger.error(f"❌ iframe 우대사항 추출 오류: {e}")
        
        return preferred

    def _extract_preferred_from_job_sections(self, user_content_soup) -> dict:
        """user_content 내에서 우대사항 섹션 추출"""
        preferred = {"raw_text": "", "raw_list": []}
        
        try:
            definition_lists = user_content_soup.find_all('dl')
            
            for dl in definition_lists:
                dt_element = dl.find('dt')
                dd_element = dl.find('dd')
                
                if dt_element and dd_element:
                    section_title = dt_element.get_text(strip=True)
                    
                    if '우대사항' in section_title or '우대조건' in section_title:
                        section_content = dd_element.get_text(strip=True)
                        
                        if section_content:
                            preferred['raw_text'] = section_content
                            preferred_list = []
                            
                            # pre 태그 내용 우선 처리
                            pre_elements = dd_element.find_all('pre')
                            for pre in pre_elements:
                                pre_text = pre.get_text(strip=True)
                                
                                if '•' in pre_text:
                                    items = [item.strip() for item in pre_text.split('•') if item.strip()]
                                elif '◦' in pre_text:
                                    items = [item.strip() for item in pre_text.split('◦') if item.strip()]
                                elif re.search(r'\n\s*-\s*', pre_text):
                                    items = [item.strip() for item in re.split(r'\n\s*-\s*', pre_text) if item.strip()]
                                elif '\n' in pre_text:
                                    items = [item.strip() for item in pre_text.split('\n') if item.strip() and len(item.strip()) > 5]
                                else:
                                    items = [pre_text] if pre_text else []
                                
                                preferred_list.extend(items)
                            
                            # pre 태그가 없으면 전체 텍스트에서 추출
                            if not preferred_list:
                                if '•' in section_content:
                                    preferred_list = [item.strip() for item in section_content.split('•') if item.strip()]
                                elif '◦' in section_content:
                                    preferred_list = [item.strip() for item in section_content.split('◦') if item.strip()]
                                else:
                                    preferred_list = [section_content] if section_content else []
                            
                            preferred['raw_list'] = preferred_list
                            return preferred
            
        except Exception as e:
            self.logger.error(f"❌ 우대사항 섹션 추출 오류: {e}")
        
        return preferred
    # ================== 핵심 파싱 로직 ==================
    
    def _load_iframe_content_with_playwright(self, iframe_url: str) -> BeautifulSoup:
        """Playwright로 iframe 내용 로드하고 user_content 반환"""
        try:
            page = self.browser_context.new_page()
            
            self.logger.debug(f"🌐 iframe 로딩: {iframe_url}")
            page.goto(iframe_url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            
            try:
                page.wait_for_selector('div.user_content', timeout=10000)
            except:
                self.logger.debug("⚠️ user_content 로딩 타임아웃")
            
            iframe_html = page.content()
            page.close()
            
            soup = BeautifulSoup(iframe_html, 'html.parser')
            
            # PDF/이미지 콘텐츠 감지
            self._detect_non_text_content(soup, iframe_url)
            
            user_content_div = soup.find('div', class_='user_content')
            
            if user_content_div:
                content_text = user_content_div.get_text(strip=True)
                self.logger.debug(f"✅ user_content 발견, 길이: {len(content_text)} 글자")
                
                # 텍스트 콘텐츠가 너무 적으면 의심스러운 케이스로 로깅
                if len(content_text) < 50:
                    self.logger.warning(f"🚨 [SUSPICIOUS] 텍스트 콘텐츠가 매우 적음 ({len(content_text)}글자): {iframe_url}")
                    self._log_suspicious_content(iframe_url, content_text, "텍스트_부족")
                
                return user_content_div
            else:
                self.logger.warning(f"⚠️ user_content div를 찾을 수 없음: {iframe_url}")
                self._log_suspicious_content(iframe_url, "", "user_content_없음")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ iframe 내용 로드 오류: {e}")
            return None

    def _detect_non_text_content(self, soup: BeautifulSoup, iframe_url: str):
        """PDF, 이미지 등 비텍스트 콘텐츠 감지 및 로깅"""
        try:
            # PDF 임베드 감지
            pdf_elements = soup.find_all(['embed', 'object', 'iframe'], 
                                       src=lambda x: x and ('.pdf' in x.lower() or 'pdf' in x.lower()))
            if pdf_elements:
                self.logger.warning(f"🚨 [PDF_DETECTED] PDF 콘텐츠 감지: {iframe_url}")
                self._log_suspicious_content(iframe_url, str(pdf_elements), "PDF_콘텐츠")
                return
            
            # 이미지 위주 콘텐츠 감지
            img_elements = soup.find_all('img')
            if len(img_elements) > 3:  # 이미지가 많으면 이미지 기반 공고일 가능성
                self.logger.warning(f"🚨 [IMAGE_HEAVY] 이미지 위주 콘텐츠 감지 ({len(img_elements)}개): {iframe_url}")
                img_srcs = [img.get('src', '') for img in img_elements[:5]]  # 상위 5개만
                self._log_suspicious_content(iframe_url, str(img_srcs), "이미지_위주")
                return
            
            # Canvas 요소 감지 (그려진 이미지일 가능성)
            canvas_elements = soup.find_all('canvas')
            if canvas_elements:
                self.logger.warning(f"🚨 [CANVAS_DETECTED] Canvas 요소 감지: {iframe_url}")
                self._log_suspicious_content(iframe_url, str(canvas_elements), "Canvas_콘텐츠")
                return
            
            # 텍스트가 거의 없고 다른 요소가 많은 경우
            user_content = soup.find('div', class_='user_content')
            if user_content:
                text_content = user_content.get_text(strip=True)
                all_elements = user_content.find_all(True)  # 모든 HTML 요소
                
                # 텍스트 대비 HTML 요소가 많으면 구조화된 비텍스트 콘텐츠일 가능성
                if len(text_content) < 100 and len(all_elements) > 10:
                    self.logger.warning(f"🚨 [STRUCTURED_NON_TEXT] 구조화된 비텍스트 콘텐츠 의심: {iframe_url}")
                    element_tags = [elem.name for elem in all_elements[:10]]
                    self._log_suspicious_content(iframe_url, f"텍스트:{len(text_content)}글자, 요소:{element_tags}", "구조화된_비텍스트")
                    
        except Exception as e:
            self.logger.debug(f"비텍스트 콘텐츠 감지 오류: {e}")

    def _log_suspicious_content(self, iframe_url: str, content_sample: str, content_type: str):
        """의심스러운 콘텐츠를 별도 로그 파일에 기록"""
        try:
            import os
            from datetime import datetime
            
            # 로그 디렉토리 생성
            log_dir = "logs/saramin_suspicious_content"
            os.makedirs(log_dir, exist_ok=True)
            
            # 날짜별 로그 파일
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(log_dir, f"suspicious_content_{today}.log")
            
            # 로그 엔트리 작성
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"""
=== {timestamp} ===
TYPE: {content_type}
URL: {iframe_url}
CONTENT_SAMPLE: {content_sample[:500]}...
{'=' * 50}
"""
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            self.logger.debug(f"📝 의심스러운 콘텐츠 로그 기록: {log_file}")
            
        except Exception as e:
            self.logger.debug(f"의심스러운 콘텐츠 로깅 오류: {e}")

    # ================== 기존 메서드들 (fallback 용도) ==================
    
    def _extract_job_title(self, metadata: dict, job_section: BeautifulSoup) -> str:
        if metadata.get('position_title'):
            return metadata.get('position_title')
        
        try:
            selectors = ['h1.tit_job', 'div.tit_area h1', 'h1', '.job_title h1']
            for selector in selectors:
                element = job_section.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        except Exception:
            pass
        
        return ""
    
    def _extract_company_name(self, metadata: dict, job_section: BeautifulSoup) -> str:
        if metadata.get('company_name'):
            return metadata.get('company_name')
        
        try:
            selectors = ['.company_name', '.cp_area .company', '.tit_company']
            for selector in selectors:
                element = job_section.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        except Exception:
            pass
        
        return ""
    
    def _extract_work_type(self, metadata: dict, job_section: BeautifulSoup) -> str:
        """근무형태 추출 - jv_summary를 우선으로 함"""
        try:
            # 1. jv_summary에서 우선 추출 (이미 main에서 처리됨)
            summary_section = job_section.find('div', class_='jv_summary')
            if summary_section:
                dl_elements = summary_section.find_all('dl')
                for dl in dl_elements:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd and dt.get_text(strip=True) == '근무형태':
                        work_type = dd.get_text(strip=True)
                        self.logger.debug(f"✅ 근무형태 추출: {work_type}")
                        return work_type
            
            # 2. fallback: 기존 방식
            work_info_section = job_section.find('div', class_='job_info')
            if work_info_section:
                dt_elements = work_info_section.find_all('dt')
                dd_elements = work_info_section.find_all('dd')
                
                for dt, dd in zip(dt_elements, dd_elements):
                    if '고용형태' in dt.get_text() or '근무형태' in dt.get_text():
                        return dd.get_text(strip=True)
                        
        except Exception as e:
            self.logger.debug(f"근무형태 추출 오류: {e}")
            
        return ""
    
    def _extract_location_info(self, metadata: dict, job_section: BeautifulSoup) -> dict:
        """위치 정보 추출 - jv_summary를 우선으로 함"""
        location_text = ""
        
        try:
            # 1. jv_summary에서 우선 추출
            summary_section = job_section.find('div', class_='jv_summary')
            if summary_section:
                dl_elements = summary_section.find_all('dl')
                for dl in dl_elements:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd and dt.get_text(strip=True) == '근무지역':
                        location_text = dd.get_text(strip=True)
                        self.logger.debug(f"✅ 근무지역 추출: {location_text}")
                        break
            
            # 2. fallback: 메타데이터
            if not location_text:
                location_text = metadata.get('location', '')
            
            # 3. fallback: work_place 클래스
            if not location_text:
                location_element = job_section.select_one('.work_place')
                if location_element:
                    location_text = location_element.get_text(strip=True)
                    
        except Exception as e:
            self.logger.debug(f"위치 정보 추출 오류: {e}")
        
        return self._normalize_location(location_text)
    
    def _extract_education(self, metadata: dict, job_section: BeautifulSoup) -> str:
        """학력 정보 추출 - jv_summary를 우선으로 함"""
        try:
            # 1. jv_summary에서 우선 추출
            summary_section = job_section.find('div', class_='jv_summary')
            if summary_section:
                dl_elements = summary_section.find_all('dl')
                for dl in dl_elements:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd and dt.get_text(strip=True) == '학력':
                        education = dd.get_text(strip=True)
                        self.logger.debug(f"✅ 학력 추출: {education}")
                        return education
            
            # 2. fallback: 메타데이터
            if metadata.get('education'):
                return metadata.get('education')
            
            # 3. fallback: qualification 섹션
            qualifications = job_section.find('div', class_='qualification')
            if qualifications:
                education_text = qualifications.get_text()
                return self._extract_education_from_text(education_text)
                
        except Exception as e:
            self.logger.debug(f"학력 정보 추출 오류: {e}")
        
        return ""
    
    def _extract_experience_info(self, metadata: dict, job_section: BeautifulSoup) -> dict:
        """경력 정보 추출 - jv_summary를 우선으로 함"""
        try:
            # 1. jv_summary에서 우선 추출
            summary_section = job_section.find('div', class_='jv_summary')
            if summary_section:
                dl_elements = summary_section.find_all('dl')
                for dl in dl_elements:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd and dt.get_text(strip=True) == '경력':
                        experience_text = dd.get_text(strip=True)
                        parsed_exp = self._parse_experience(experience_text)
                        self.logger.debug(f"✅ 경력 추출: {experience_text} -> {parsed_exp}")
                        return parsed_exp
            
            # 2. fallback: 메타데이터
            if metadata.get('career'):
                return self._parse_experience(metadata.get('career'))
            
            # 3. fallback: qualification 섹션
            qualifications = job_section.find('div', class_='qualification')
            if qualifications:
                career_text = qualifications.get_text()
                return self._parse_experience(career_text)
                
        except Exception as e:
            self.logger.debug(f"경력 정보 추출 오류: {e}")
        
        return {"raw_text": "", "min_years": 0, "max_years": 100}
    
    def _extract_position_info(self, metadata: dict, job_section: BeautifulSoup) -> dict:
        """포지션 정보 추출 및 정규화"""
        position_raw = {
            "raw_text": "",
            "raw_list": metadata.get('job_sectors', [])
        }
        
        # 직무 분야가 있으면 활용
        if position_raw["raw_list"]:
            position_raw["raw_text"] = ', '.join(position_raw["raw_list"])
        
        # soup에서 추가 정보
        try:
            job_category = job_section.find('div', class_='job_sector')
            if job_category:
                sectors = [span.get_text(strip=True) for span in job_category.find_all('span')]
                if sectors:
                    position_raw["raw_list"].extend(sectors)
                    position_raw["raw_text"] = ', '.join(position_raw["raw_list"])
        except Exception:
            pass
        
        # 정규화 적용
        return normalize_position_data(
            position_raw["raw_text"], 
            position_raw["raw_list"]
        )
    
    def _extract_company_info(self, job_section: BeautifulSoup, company_name: str, metadata: dict) -> dict:
        """회사 정보 추출 - jv_company 섹션의 info_area에서 추출"""
        company = {
            "name": company_name,
            "size": "",
            "description": "",
            "sales": "",
            "industry": ""
        }
        
        try:
            # jv_company 섹션의 info_area에서 추출
            company_section = job_section.find('div', class_='jv_company')
            if company_section:
                info_area = company_section.find('div', class_='info_area')
                if info_area:
                    info_items = info_area.find_all('dl')
                    
                    for item in info_items:
                        dt = item.find('dt')
                        dd = item.find('dd')
                        
                        if dt and dd:
                            key = dt.get_text(strip=True)
                            value = dd.get_text(strip=True)
                            
                            if '업종' in key:
                                company['industry'] = value
                                self.logger.debug(f"✅ 회사 업종: {value}")
                            elif '기업형태' in key:
                                company['size'] = value
                                self.logger.debug(f"✅ 회사 규모/형태: {value}")
                            elif '사원수' in key:
                                # 기존 size가 없으면 사원수로, 있으면 추가
                                if not company['size']:
                                    company['size'] = value
                                else:
                                    company['size'] += f", {value}"
                                self.logger.debug(f"✅ 회사 사원수: {value}")
                            elif '설립일' in key:
                                if company['description']:
                                    company['description'] += f", 설립: {value}"
                                else:
                                    company['description'] = f"설립: {value}"
                                self.logger.debug(f"✅ 회사 설립일: {value}")
                            elif '매출' in key:
                                company['sales'] = value
                                self.logger.debug(f"✅ 회사 매출: {value}")
            
            # fallback: 기존 cp_info 방식
            if not any([company['size'], company['industry'], company['description']]):
                company_info = job_section.find('div', class_='cp_info')
                if company_info:
                    info_items = company_info.find_all('dl')
                    
                    for item in info_items:
                        dt = item.find('dt')
                        dd = item.find('dd')
                        
                        if dt and dd:
                            key = dt.get_text(strip=True)
                            value = dd.get_text(strip=True)
                            
                            if '업종' in key:
                                company['industry'] = value
                            elif '규모' in key or '사원수' in key:
                                company['size'] = value
                            elif '매출' in key:
                                company['sales'] = value
                            elif '설립' in key:
                                if company['description']:
                                    company['description'] += f", 설립: {value}"
                                else:
                                    company['description'] = f"설립: {value}"
            
            # 메타데이터에서 추가 정보
            if metadata.get('company_type'):
                if company['description']:
                    company['description'] += f", {metadata['company_type']}"
                else:
                    company['description'] = metadata['company_type']
                    
        except Exception as e:
            self.logger.debug(f"회사 정보 추출 오류: {e}")
        
        return company