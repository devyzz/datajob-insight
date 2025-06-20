from pymongo import MongoClient, UpdateOne
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
        """JobPostingModel 저장 (upsert 방식으로 성능 최적화)"""
        try:
            job_dict = job_posting.to_dict()
            
            # job_url 기준으로 upsert (기존 동작과 동일한 결과)
            result = self.job_postings_collection.replace_one(
                {"job_url": job_dict["job_url"]},
                job_dict,
                upsert=True
            )
            
            if result.upserted_id:
                # 새로 생성된 경우
                return str(result.upserted_id)
            else:
                # 기존 문서가 업데이트된 경우 (중복)
                return None
                
        except Exception as e:
            # 다른 에러는 그대로 전파 (기존 동작 유지)
            raise e
    
    def bulk_save_job_postings(self, job_postings: list) -> dict:
        """대량 저장 메서드 (새로 추가 - 성능 최적화용)"""
        if not job_postings:
            return {"inserted": 0, "updated": 0, "errors": 0}
            
        try:
            operations = []
            for job_posting in job_postings:
                job_dict = job_posting.to_dict()
                
                operations.append(
                    UpdateOne(
                        {"job_url": job_dict["job_url"]},
                        {"$set": job_dict},
                        upsert=True
                    )
                )
            
            # 대량 실행 (ordered=False로 에러가 있어도 계속 진행)
            result = self.job_postings_collection.bulk_write(operations, ordered=False)
            
            return {
                "inserted": result.upserted_count,
                "updated": result.modified_count,
                "errors": len(result.bulk_api_result.get("writeErrors", []))
            }
            
        except Exception as e:
            self.logger.error(f"대량 저장 실패: {e}")
            raise e
    
    def get_existing_job_urls(self, platform: str, days_back: int) -> set:
        """기존 채용공고 URL 조회 (메모리 효율성 최적화)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # 배치 크기를 제한해서 메모리 사용량 최적화
            cursor = self.job_postings_collection.find(
                {
                    "platform": platform,
                    "crawled_at": {"$gte": cutoff_date}
                },
                {"job_url": 1}
            ).batch_size(1000)  # 배치 크기 제한
            
            urls = set()
            batch_count = 0
            
            for doc in cursor:
                urls.add(doc["job_url"])
                batch_count += 1
                
                # 메모리 사용량 모니터링 (10만개 이상이면 경고)
                if batch_count % 100000 == 0:
                    self.logger.warning(f"대량 URL 로딩 중: {batch_count:,}개 처리됨")
            
            if batch_count > 0:
                self.logger.info(f"기존 URL {len(urls):,}개 로딩 완료 (플랫폼: {platform})")
            
            return urls
            
        except Exception as e:
            self.logger.error(f"기존 URL 조회 실패: {e}")
            return set()
    
    def check_job_exists_fast(self, job_url: str) -> bool:
        """빠른 공고 존재 여부 확인 (새로 추가)"""
        try:
            result = self.job_postings_collection.find_one(
                {"job_url": job_url},
                {"_id": 1}  # _id만 조회해서 성능 최적화
            )
            return result is not None
        except Exception as e:
            self.logger.error(f"공고 존재 여부 확인 실패: {e}")
            return False
    
    def get_recent_urls_count(self, platform: str, days_back: int = 7) -> int:
        """최근 공고 수만 조회 (메모리 효율적)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            count = self.job_postings_collection.count_documents({
                "platform": platform,
                "crawled_at": {"$gte": cutoff_date}
            })
            
            return count
        except Exception as e:
            self.logger.error(f"최근 공고 수 조회 실패: {e}")
            return 0
    
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
            site_collections = ['wanted_job_postings', 'jobkorea_job_postings', 'saramin_job_postings']
            
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
    
    def cleanup_old_postings(self, days_to_keep: int = 90) -> int:
        """오래된 공고 정리 (새로 추가 - 성능 유지용)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            result = self.job_postings_collection.delete_many({
                "crawled_at": {"$lt": cutoff_date}
            })
            
            if result.deleted_count > 0:
                self.logger.info(f"오래된 공고 {result.deleted_count}개 삭제 (컬렉션: {self.job_postings_collection.name})")
            
            return result.deleted_count
            
        except Exception as e:
            self.logger.error(f"오래된 공고 정리 실패: {e}")
            return 0
    
    def get_performance_stats(self) -> dict:
        """성능 통계 조회 (새로 추가)"""
        try:
            # 컬렉션 크기 및 인덱스 정보
            stats = self.db.command("collStats", self.job_postings_collection.name)
            
            return {
                "collection_name": self.job_postings_collection.name,
                "document_count": stats.get("count", 0),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "index_count": stats.get("nindexes", 0),
                "index_size_mb": round(stats.get("totalIndexSize", 0) / (1024 * 1024), 2)
            }
        except Exception as e:
            self.logger.error(f"성능 통계 조회 실패: {e}")
            return {}
    
    # TODO: 나중에 구현할 기능들
    # def save_error_log(self, error_data: dict) -> str:
    #     """에러 로그 저장 (나중에 구현)"""
    #     pass
    
    # def save_pdf_url(self, pdf_data: dict) -> str:
    #     """PDF URL 저장 (나중에 구현)"""
    #     pass