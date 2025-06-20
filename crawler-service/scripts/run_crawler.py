#!/usr/bin/env python3
"""
크롤러 실행 스크립트
"""
import sys
sys.path.append('.')

from crawler.job_crawler import JobCrawler

def main():
    """기본 크롤링 (신규만)"""
    with JobCrawler() as crawler:
        sites = ['wanted', 'saramin', 'jobkorea']
        
        print("🚀 3개 사이트 크롤링 시작 (신규만)...")
        
        total_results = {}
        
        for site in sites:
            print(f"\n📍 {site.upper()} 크롤링 중...")
            try:
                result = crawler.crawl_site(site, full_crawl=False)
                result.print_summary()
                total_results[site] = result
            except Exception as e:
                print(f"❌ {site} 크롤링 실패: {e}")
        
        # 전체 요약
        print("\n" + "="*50)
        print("🎯 전체 크롤링 결과 요약:")
        total_new = sum(r.new_saved for r in total_results.values())
        total_time = sum(r.execution_time for r in total_results.values())
        
        print(f"   ✅ 총 신규 저장: {total_new}개")
        print(f"   ⏱️  총 소요시간: {total_time:.1f}초")

def full_crawl():
    """전체 크롤링 (모든 데이터)"""
    with JobCrawler() as crawler:
        sites = ['wanted', 'saramin', 'jobkorea']
        
        print("🚀 3개 사이트 전체 크롤링 시작...")
        print("⚠️  주의: 시간이 오래 걸릴 수 있습니다!")
        
        total_results = {}
        
        for site in sites:
            print(f"\n📍 {site.upper()} 전체 크롤링 중...")
            try:
                result = crawler.crawl_site(site, full_crawl=True)
                result.print_summary()
                total_results[site] = result
            except Exception as e:
                print(f"❌ {site} 크롤링 실패: {e}")
        
        # 전체 요약
        print("\n" + "="*50)
        print("🎯 전체 크롤링 결과 요약:")
        total_new = sum(r.new_saved for r in total_results.values())
        total_time = sum(r.execution_time for r in total_results.values())
        
        print(f"   ✅ 총 저장: {total_new}개")
        print(f"   ⏱️  총 소요시간: {total_time:.1f}초")

def test_single_site(site_name: str, full: bool = False):
    """단일 사이트 테스트"""
    with JobCrawler() as crawler:
        crawl_type = "전체" if full else "신규"
        print(f"🧪 {site_name} {crawl_type} 크롤링 테스트...")
        result = crawler.crawl_site(site_name, full_crawl=full)
        result.print_summary()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'full':
            full_crawl()
        elif command in ['wanted', 'saramin', 'jobkorea']:
            full = len(sys.argv) > 2 and sys.argv[2] == 'full'
            test_single_site(command, full)
        else:
            print("Usage: python scripts/run_crawler.py [full|wanted|saramin|jobkorea] [full]")
    else:
        main()