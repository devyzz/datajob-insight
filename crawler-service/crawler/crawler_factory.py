from crawler.wanted_crawler import WantedCrawler
from crawler.jobkorea_crawler import JobkoreaCrawler
from crawler.saramin_crawler import SaraminCrawler
from crawler.base_crawler import JobCrawler
import logging

class CrawlerFactory:
    """
    크롤러 팩토리 클래스
    
    사이트별로 적절한 크롤러 인스턴스를 생성하여 반환
    """
    
    @staticmethod
    def create_crawler(site_name: str) -> JobCrawler:
        """
        사이트명에 따라 적절한 크롤러 인스턴스 생성
        
        Args:
            site_name: 크롤링할 사이트명 ('wanted', 'jobkorea', 'saramin')
            
        Returns:
            해당 사이트의 크롤러 인스턴스
        """
        if site_name == 'wanted':
            return WantedCrawler(site_name)
        elif site_name == 'jobkorea':
            return JobkoreaCrawler(site_name)
        elif site_name == 'saramin':
            return SaraminCrawler(site_name)
        else:
            raise ValueError(f"지원하지 않는 사이트입니다: {site_name}")
    
    @staticmethod
    def get_supported_sites() -> list:
        """
        지원하는 사이트 목록 반환
        
        Returns:
            지원하는 사이트명 리스트
        """
        return ['wanted', 'jobkorea', 'saramin']