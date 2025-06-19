from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import os

class DatabaseManager:
    def __init__(self, connection_string: str = None, site_name: str = None):
        if connection_string is None:
            connection_string = os.getenv('CRAWLER_SERVICE_MONGODB_URI', 'mongodb://localhost:27017/')
        
        self.client = MongoClient(connection_string)
        self.db = self.client.job_crawler
        self.site_name = site_name
        
        # 사이트별 JobPostingModel용 컬렉션
        if site_name:
            collection_name = f"{site_name}_job_postings"
            self.job_postings_collection = self.db[collection_name]
        else:
            # 기본값 (하위 호환성)
            self.job_postings_collection = self.db.job_postings
        
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
        
        # 인덱스 생성
        self._create_indexes()
    
    def _create_indexes(self):
        """필요한 인덱스 생성"""
        # job_postings 컬렉션 인덱스 : 자주 검색하거나 정렬하거나 중복 검사를 하는 필드에 인덱스 생성
        
        try:
            # 공고 URL 중복 검사, 사용예) find_one({"job_url": url})
            self.job_postings_collection.create_index("job_url", unique=True) 
            
            # 공고 ID 중복 검사, ID는 나중에 연계 시스템에서 PK처럼 활용 가능
            self.job_postings_collection.create_index("job_id", unique=True) 
            
            # 회사명 검색, 사용예) find({"company.name": "회사명"})
            self.job_postings_collection.create_index([("company.name", 1)]) 
            
            # 플랫폼별 최신 공고 검색, 사용예) find({"platform": "플랫폼명"}).sort("crawled_at", -1)
            self.job_postings_collection.create_index([("platform", 1), ("crawled_at", -1)]) 
            
            # 플랫폼별 공고 제목 검색, 사용예) find({"platform": "플랫폼명", "job_title": "공고 제목"})
            self.job_postings_collection.create_index([("platform", 1), ("job_title", "text")]) 
            
            self.logger.info("✅ Database indexes created successfully")
        except Exception as e:
            self.logger.warning(f"⚠️ Index creation warning: {e}")
    
    def save_job_posting(self, job_posting) -> str:
        """JobPostingModel 저장"""
        try:
            result = self.job_postings_collection.insert_one(job_posting.to_dict())
            return str(result.inserted_id)
        except Exception as e:
            if "duplicate key" in str(e):
                return None  # 중복
            else:
                raise e
    
    def get_existing_job_urls(self, platform: str, days_back: int) -> set:
        """기존 채용공고 URL 조회"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        cursor = self.job_postings_collection.find(
            {
                "platform": platform,
                "crawled_at": {"$gte": cutoff_date}
            },
            {"job_url": 1}
        )
        
        return {doc["job_url"] for doc in cursor}
    
    def get_job_stats(self) -> dict:
        """채용공고 통계 조회"""
        if self.site_name:
            # 특정 사이트의 통계만 조회
            pipeline = [
                {"$group": {
                    "_id": "$platform",
                    "count": {"$sum": 1},
                    "latest": {"$max": "$crawled_at"}
                }},
                {"$sort": {"count": -1}}
            ]
            return list(self.job_postings_collection.aggregate(pipeline))
        else:
            # 모든 사이트의 통계 조회
            all_stats = []
            
            # 알려진 사이트별 컬렉션들 조회
            site_collections = ['wanted_job_postings', 'jobkorea_job_postings']
            
            for collection_name in site_collections:
                try:
                    collection = self.db[collection_name]
                    pipeline = [
                        {"$group": {
                            "_id": "$platform",
                            "count": {"$sum": 1},
                            "latest": {"$max": "$crawled_at"}
                        }},
                        {"$sort": {"count": -1}}
                    ]
                    
                    site_stats = list(collection.aggregate(pipeline))
                    for stat in site_stats:
                        stat['collection'] = collection_name
                    all_stats.extend(site_stats)
                except Exception as e:
                    self.logger.debug(f"컬렉션 {collection_name} 조회 실패: {e}")
            
            return all_stats
    
    def find_job_by_url(self, job_url: str):
        """URL로 채용공고 조회"""
        return self.job_postings_collection.find_one({"job_url": job_url})
    
    def update_job_posting(self, job_id: str, update_data: dict) -> bool:
        """채용공고 업데이트"""
        try:
            result = self.job_postings_collection.update_one(
                {"job_id": job_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"❌ Job posting update failed: {e}")
            return False
    
    # TODO: 나중에 구현할 기능들
    # def save_error_log(self, error_data: dict) -> str:
    #     """에러 로그 저장 (나중에 구현)"""
    #     pass
    
    # def save_pdf_url(self, pdf_data: dict) -> str:
    #     """PDF URL 저장 (나중에 구현)"""
    #     pass