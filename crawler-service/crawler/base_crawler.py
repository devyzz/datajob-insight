import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from urllib.parse import urlencode, urljoin, urlparse
import random
import re
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
import os

from config.site_configs import SITE_CONFIGS, CrawlMethod, CRAWL_DAYS_BACK
from models.data_models import JobPostingModel
from utils.database import DatabaseManager

from utils.position_normalizer import normalize_position_data

@dataclass
class CrawlResult:
    site_name: str
    total_found: int
    new_saved: int
    duplicates: int
    errors: int
    execution_time: float
    logger: logging.Logger
    
    def print_summary(self):
        self.logger.info(f"   🎯 {self.site_name} 크롤링 완료:")
        self.logger.info(f"   📊 총 발견: {self.total_found}개")
        self.logger.info(f"   ✅ 신규 저장: {self.new_saved}개")
        self.logger.info(f"   ⚪ 중복: {self.duplicates}개")
        self.logger.info(f"   ❌ 에러: {self.errors}개")
        self.logger.info(f"   ⏱️  소요시간: {self.execution_time:.1f}초")
        self.logger.info(f"================================================")


class JobCrawler(ABC):
    """
    채용공고 크롤러 베이스 클래스
    
    공통 기능:
    - 크롤링 실행 흐름 관리 (crawl_site)
    - 리소스 관리 (Playwright, HTTP 세션)
    - 로깅 설정
    - 데이터베이스 연동
    - 유틸리티 메서드들
    
    자식 클래스에서 구현해야 할 메서드:
    - _get_job_urls: 사이트별 URL 수집 로직
    - _crawl_job_detail: 사이트별 상세 크롤링 로직
    """
    
    def __init__(self, site_name: str):
        self.db_manager = DatabaseManager(site_name=site_name)
        
        # HTTP 세션 설정 (requests용)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Playwright 인스턴스 (필요시 생성)
        self.playwright = None
        self.browser = None
    
        self.site_name = site_name
        
        # 로깅 설정
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        log_dir = f'logs/{current_time}'
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/crawler_{self.site_name}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """리소스 정리"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _init_playwright(self, config):
        """Playwright 초기화 (필요시에만)"""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=config.playwright_options.get('headless', True)
            )
    
    def crawl_site(self, site_name: str, full_crawl: bool = False) -> CrawlResult:
        """
        사이트 크롤링 실행
        """
        start_time = time.time()
        config = SITE_CONFIGS[site_name]
        
        self.logger.info(f"================================================")
        self.logger.info(f"🚀 {site_name} 크롤링 시작 - {datetime.now()}")
        self.logger.info(f"🌐 Base URL: {config.base_url}")
        
        #1: 기존 URL 조회 (중복 방지)
        existing_urls = self.db_manager.get_existing_job_urls(site_name, CRAWL_DAYS_BACK) if not full_crawl else set()
        self.logger.info(f"📚 {site_name}: {len(existing_urls)}개 기존 URL 발견")
        
        #2: 채용공고 목록에서 URL 수집 (자식 클래스에서 구현)
        job_urls = self._get_job_urls(config, full_crawl)
        
        #3: 신규 URL 필터링
        #new_urls = [url for url in job_urls if url not in existing_urls]
        new_urls = job_urls #시험용으로 중복 제거 비활성화
        
        self.logger.info(f"🆕 {site_name}: {len(new_urls)}개 신규 URL (총 {len(job_urls)}개 중)")
        
        #4: 개별 페이지 크롤링 (자식 클래스에서 구현)
        new_saved = 0
        duplicates = len(job_urls) - len(new_urls)
        errors = 0
        
        for i, url in enumerate(new_urls, 1):
            try:
                job_posting = self._crawl_job_detail(url, config)
                
                if job_posting:
                    # JobPostingModel을 dict로 변환해서 저장
                    doc_id = self.db_manager.save_job_posting(job_posting)
                    
                    if doc_id:
                        new_saved += 1
                        company_name = job_posting.company.get('name', 'Unknown')
                        self.logger.info(f"✅ Saved: [{company_name}] {job_posting.job_title} - {url}")
                    else:
                        self.logger.info(f"⚪ Duplicate: {url}")
                
                # 진행상황 출력
                if i % 5 == 0:
                    self.logger.info(f"📈 {site_name}: {i}/{len(new_urls)} processed")
                
            except Exception as e:
                self.logger.error(f"❌ Error processing {url}: {e}")
                errors += 1
        
        execution_time = time.time() - start_time
        
        return CrawlResult(
            site_name=site_name,
            total_found=len(job_urls),
            new_saved=new_saved,
            duplicates=duplicates,
            errors=errors,
            execution_time=execution_time, 
            logger=self.logger
        )
    
    @abstractmethod
    def _get_job_urls(self, config, full_crawl: bool = False) -> list:
        """
        채용공고 URL 수집 (사이트별 구현 필요)
        
        Args:
            config: 사이트 설정
            full_crawl: 전체 크롤링 여부
            
        Returns:
            채용공고 URL 리스트
        """
        pass
    
    @abstractmethod
    def _crawl_job_detail(self, url: str, config) -> JobPostingModel:
        """
        개별 채용공고 크롤링 (사이트별 구현 필요)
        
        Args:
            url: 채용공고 URL
            config: 사이트 설정
            
        Returns:
            JobPostingModel 객체
        """
        pass

    # ================== 공통 유틸리티 메서드들 ==================
    
    def _get_common_headers(self, config, referer: str = None) -> dict:
        """공통 헤더 생성"""
        headers = config.common_headers.copy() if config.common_headers else {}
        if referer:
            headers['Referer'] = referer
        return headers
    
    def _normalize_url(self, href: str, base_url: str) -> str:
        """URL 정규화"""
        if not href:
            return ""
        
        if href.startswith('http'):
            return href
        elif href.startswith('//'):
            return f"https:{href}"
        elif href.startswith('/'):
            return urljoin(base_url, href)
        else:
            return urljoin(base_url, f"/{href}")

    def _normalize_location(self, location_text: str) -> dict:
        """위치 정보를 정규화하여 딕셔너리 형태로 반환"""
        if not location_text:
            return {"raw_text": "", "city": "", "district": ""}
        
        # 기본 정규화 로직
        location = {
            "raw_text": location_text,
            "city": "",
            "district": ""
        }
        
        try:
            # 간단한 파싱 (서울, 경기, 부산 등)
            if "서울" in location_text:
                location["city"] = "서울"
                # 구 정보 추출 (예: 강남구, 서초구 등)
                import re
                district_match = re.search(r'([가-힣]+구)', location_text)
                if district_match:
                    location["district"] = district_match.group(1)
            elif "경기" in location_text:
                location["city"] = "경기"
            elif "부산" in location_text:
                location["city"] = "부산"
            elif "대구" in location_text:
                location["city"] = "대구"
            elif "인천" in location_text:
                location["city"] = "인천"
            elif "광주" in location_text:
                location["city"] = "광주"
            elif "대전" in location_text:
                location["city"] = "대전"
            elif "울산" in location_text:
                location["city"] = "울산"
            
        except Exception:
            pass
        
        return location
    
    def _parse_experience(self, exp_text: str) -> dict:
        """경력 정보 파싱 (공통 로직)"""
        experience = {"raw_text": exp_text, "min_years": 0, "max_years": 0}
        
        if not exp_text:
            return experience
            
        # 신입 체크
        if any(keyword in exp_text for keyword in ["신입", "경력무관"]):
            experience["min_years"] = 0
            experience["max_years"] = 0
            return experience
        
        # 숫자 추출
        numbers = re.findall(r'(\d+)', exp_text)
        if numbers:
            numbers = [int(n) for n in numbers]
            
            if "이상" in exp_text:
                experience["min_years"] = numbers[0]
                experience["max_years"] = 99
            elif len(numbers) >= 2:
                experience["min_years"] = min(numbers)
                experience["max_years"] = max(numbers)
            elif len(numbers) == 1:
                experience["min_years"] = numbers[0]
                experience["max_years"] = numbers[0]
        
        return experience
    
    # def _extract_techs_from_text(self, text: str) -> list:
    #     """텍스트에서 기술스택 키워드 추출 (공통 로직)"""
    #     if not text:
    #         return []
        
    #     # 확장된 기술스택 키워드들
    #     tech_keywords = [
    #         # 언어
    #         'JavaScript', 'TypeScript', 'Python', 'Java', 'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin',
    #         'PHP', 'Ruby', 'Scala', 'Dart', 'HTML', 'CSS',
            
    #         # 프레임워크/라이브러리
    #         'Node.js', 'React', 'Vue.js', 'Vue', 'Angular', 'Nest.js', 'NestJS', 'Express', 'Express.js',
    #         'Spring', 'Spring Boot', 'Django', 'Flask', 'FastAPI', 'Next.js', 'NextJS', 'Nuxt.js',
    #         'jQuery', 'Bootstrap', 'Tailwind', 'Flutter', 'React Native',
            
    #         # 데이터베이스
    #         'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite', 'MariaDB', 'Elasticsearch',
    #         'DynamoDB', 'Cassandra', 'InfluxDB',
            
    #         # 클라우드/인프라
    #         'AWS', 'Azure', 'GCP', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI',
    #         'GitHub Actions', 'Terraform', 'Ansible', 'Nginx', 'Apache',
            
    #         # 메시징/큐
    #         'RabbitMQ', 'Kafka', 'Apache Kafka', 'SQS', 'Pub/Sub',
            
    #         # 모니터링/로깅
    #         'Elastic Stack', 'ELK', 'Prometheus', 'Grafana', 'CloudWatch', 'DataDog',
            
    #         # API/통신
    #         'REST', 'RESTful', 'GraphQL', 'gRPC', 'WebSocket', 'Socket.io',
            
    #         # 방법론/도구
    #         'Git', 'GitHub', 'GitLab', 'TDD', 'BDD', 'Agile', 'Scrum', 'CI/CD', 'DevOps',
    #         'Microservice', 'MSA', 'Serverless', 'Container'
    #     ]
        
    #     found_techs = []
    #     text_lower = text.lower()
        
    #     for tech in tech_keywords:
    #         # 대소문자 구분 없이 검색
    #         if tech.lower() in text_lower:
    #             # 정확한 매칭을 위해 단어 경계 체크
    #             pattern = r'\b' + re.escape(tech.lower()) + r'\b'
    #             if re.search(pattern, text_lower):
    #                 found_techs.append(tech)
        
    #     return found_techs
    
    def _extract_techs_from_text(self, text: str) -> list:
        """텍스트에서 기술스택 키워드 추출 (대폭 확장된 250개+ 키워드)"""
        if not text:
            return []
        
        tech_keywords = [
            # 프로그래밍 언어
            'JavaScript', 'TypeScript', 'Python', 'Java', 'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin',
            'PHP', 'Ruby', 'Scala', 'Dart', 'HTML', 'CSS', 'SQL', 'R', 'MATLAB', 'Objective-C',
            
            # 웹 프레임워크/라이브러리
            'Node.js', 'React', 'Vue.js', 'Vue', 'Angular', 'Nest.js', 'NestJS', 'Express', 'Express.js',
            'Spring', 'Spring Boot', 'Django', 'Flask', 'FastAPI', 'Next.js', 'NextJS', 'Nuxt.js',
            'jQuery', 'Bootstrap', 'Tailwind', 'Tailwind CSS', 'Material-UI', 'Ant Design',
            'Laravel', 'CodeIgniter', 'Symfony', 'CakePHP', 'Rails', 'Ruby on Rails',
            
            # 모바일 개발
            'Flutter', 'React Native', 'Xamarin', 'Ionic', 'PhoneGap', 'Cordova',
            # iOS 전용 (테스트에서 성공한 키워드들)
            'SwiftUI', 'UIKit', 'Combine', 'SnapKit', 'Swift Concurrency', 'RxSwift', 'Alamofire',
            'Core Data', 'CloudKit', 'WebKit', 'MapKit', 'AVFoundation', 'ARKit', 'Core ML',
            'Auto Layout', 'AutoLayout', 'Storyboard', 'XIB', 'MVVM', 'MVP', 'MVC', 'VIPER',
            'SPM', 'CocoaPods', 'Carthage', 'Xcode', 'Instruments', 'TestFlight', 'App Store Connect',
            'Xcode Cloud', 'Firebase', 'Realm', 'SQLite', 'UserNotifications', 'Push Notifications',
            # Android 전용
            'Android Studio', 'Gradle', 'Retrofit', 'OkHttp', 'Glide', 'Picasso', 'Room', 'LiveData',
            'ViewModel', 'Data Binding', 'View Binding', 'Jetpack Compose', 'Coroutines', 'RxJava',
            'Dagger', 'Hilt', 'Koin', 'Material Design', 'ConstraintLayout',
            
            # 데이터베이스
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite', 'MariaDB', 'Elasticsearch',
            'DynamoDB', 'Cassandra', 'InfluxDB', 'Neo4j', 'CouchDB', 'Firebase Firestore',
            'Microsoft SQL Server', 'DB2', 'Supabase', 'PlanetScale',
            
            # 클라우드/인프라
            'AWS', 'Azure', 'GCP', 'Google Cloud', 'Digital Ocean', 'Heroku', 'Vercel', 'Netlify',
            'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI', 'GitHub Actions', 'CircleCI', 'Travis CI',
            'Terraform', 'Ansible', 'Chef', 'Puppet', 'Vagrant', 'Nginx', 'Apache', 'HAProxy',
            'CloudFlare', 'CDN', 'Load Balancer',
            
            # 메시징/큐
            'RabbitMQ', 'Kafka', 'Apache Kafka', 'SQS', 'Pub/Sub',
            
            # 모니터링/로깅
            'Elastic Stack', 'ELK', 'Prometheus', 'Grafana', 'CloudWatch', 'DataDog',
            
            # API/통신
            'REST', 'RESTful', 'GraphQL', 'gRPC', 'WebSocket', 'Socket.io',
            
            # 기타 도구/기술들
            'Git', 'GitHub', 'GitLab', 'TDD', 'BDD', 'Agile', 'Scrum', 'CI/CD', 'DevOps',
            'Microservice', 'MSA', 'Serverless', 'Container'
        ]
        
        found_techs = []
        text_lower = text.lower()
        
        for tech in tech_keywords:
            tech_lower = tech.lower()
            pattern = r'\b' + re.escape(tech_lower) + r'\b'
            
            if re.search(pattern, text_lower):
                original_match = re.search(pattern, text_lower)
                if original_match:
                    start, end = original_match.span()
                    actual_text = text[start:end]
                    found_techs.append(actual_text if actual_text else tech)
        
        return found_techs
    
    def _extract_education_from_text(self, requirements: str) -> str:
        """텍스트에서 학력 정보 추출 (공통 로직)"""
        if not requirements:
            return None
        
        requirements_lower = requirements.lower()
        
        if '학력무관' in requirements_lower or '무관' in requirements_lower:
            return '무관'
        elif '고등학교' in requirements_lower:
            return '고졸'
        elif '학사' in requirements_lower:
            return '대졸'
        elif '석사' in requirements_lower:
            return '석사'
        elif '박사' in requirements_lower:
            return '박사'
        
        return ''