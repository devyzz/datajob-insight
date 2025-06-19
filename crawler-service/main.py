#!/usr/bin/env python3
"""
채용공고 크롤러 메인 실행 스크립트
"""

import argparse
import logging
import os
from datetime import datetime

from crawler.crawler_factory import CrawlerFactory
from crawler.base_crawler import CrawlResult


def setup_logging(log_level: str, site_name: str) -> logging.Logger:
    """로깅 설정"""
    # 로그 레벨 매핑
    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    log_level_int = level_mapping.get(log_level.upper(), logging.INFO)
    
    # 로그 디렉토리 생성
    current_time = datetime.now().strftime('%Y%m%d_%H%M')
    log_dir = f'logs/{current_time}'
    os.makedirs(log_dir, exist_ok=True)
    
    # 로깅 설정
    logging.basicConfig(
        level=log_level_int,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/crawler_{site_name}.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"로그 레벨: {log_level.upper()}")
    return logger


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='채용공고 크롤러')
    parser.add_argument('--site', required=True, 
                       choices=CrawlerFactory.get_supported_sites(),
                       help='크롤링할 사이트 선택')
    parser.add_argument('--full', action='store_true',
                       help='전체 크롤링 (기본값: 신규만)')
    parser.add_argument('--mongodb-uri', 
                       default=None,
                       help='MongoDB 연결 URI (기본값: 환경변수 또는 localhost)')
    parser.add_argument('--log-level',
                       default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='로그 레벨 (기본값: INFO)')
    
    args = parser.parse_args()
    
    try:
        # MongoDB URI 환경변수 설정 (인자가 제공된 경우)
        if args.mongodb_uri:
            os.environ['CRAWLER_SERVICE_MONGODB_URI'] = args.mongodb_uri
            print(f"✅ MongoDB URI 설정: {args.mongodb_uri}")
        
        # 로그 레벨 환경변수 설정
        os.environ['LOG_LEVEL'] = args.log_level.upper()
        
        # 로깅 설정
        logger = setup_logging(args.log_level, args.site)
        
        # 실행 정보 출력
        logger.info(f"🚀 {args.site} 크롤러 시작")
        logger.info(f"📊 MongoDB URI: {os.getenv('CRAWLER_SERVICE_MONGODB_URI', 'mongodb://localhost:27017/')}")
        logger.info(f"🔧 실행 모드: {'전체 크롤링' if args.full else '신규만'}")
        logger.info(f"📋 로그 레벨: {args.log_level.upper()}")
        
        # 크롤러 생성
        crawler = CrawlerFactory.create_crawler(args.site)
        
        with crawler:
            # 크롤링 실행
            result = crawler.crawl_site(args.site, full_crawl=args.full)
            
            # 결과 출력
            result.print_summary()
            
    except Exception as e:
        print(f"❌ 크롤링 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()