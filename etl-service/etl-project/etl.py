import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import psycopg2

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# MongoDB 연결
mongo = MongoClient(os.getenv("MONGO_URI"))
mdb = mongo[os.getenv("MONGO_DB")]

# PostgreSQL 연결
pg_conn = psycopg2.connect(
    dbname=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASS"),
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT")
)
pg_cur = pg_conn.cursor()

# DDL 생성
ddl_statements = [
    """
    CREATE TABLE IF NOT EXISTS platform (
        platform_id SERIAL PRIMARY KEY,
        platform_name VARCHAR(50) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS company (
        company_id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE,
        size VARCHAR(20),
        industry VARCHAR(100),
        description TEXT,
        sales VARCHAR(50)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS job_postings (
        posting_id BIGSERIAL PRIMARY KEY,
        platform_id INT REFERENCES platform(platform_id),
        company_id INT REFERENCES company(company_id),
        job_id VARCHAR(50) UNIQUE,
        title VARCHAR(200),
        job_type VARCHAR(50),
        location VARCHAR(100),
        experience_min INT,
        experience_max INT,
        education VARCHAR(20),
        url VARCHAR(500),
        crawled_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS skill (
        skill_id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS job_posting_skill (
        posting_id BIGINT REFERENCES job_postings(posting_id),
        company_id INT REFERENCES company(company_id),
        skill_id INT REFERENCES skill(skill_id),
        platform_id INT REFERENCES platform(platform_id),
        PRIMARY KEY (posting_id, skill_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS log (
        log_id SERIAL PRIMARY KEY,
        log_data TEXT,
        log_date TIMESTAMP DEFAULT NOW()
    )
    """
]

for stmt in ddl_statements:
    pg_cur.execute(stmt)
pg_conn.commit()

def upsert_platform(name):
    pg_cur.execute(
        "INSERT INTO platform (platform_name) VALUES (%s) ON CONFLICT DO NOTHING",
        (name,)
    )
    pg_cur.execute("SELECT platform_id FROM platform WHERE platform_name = %s", (name,))
    return pg_cur.fetchone()[0]

def upsert_company(info):
    pg_cur.execute(
        """
        INSERT INTO company (name, size, industry, description, sales)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE
          SET size = EXCLUDED.size,
              industry = EXCLUDED.industry,
              description = EXCLUDED.description,
              sales = EXCLUDED.sales
        """,
        (info.get("name"), info.get("size"), info.get("industry"),
         info.get("description"), info.get("sales"))
    )
    pg_cur.execute("SELECT company_id FROM company WHERE name = %s", (info.get("name"),))
    return pg_cur.fetchone()[0]

def upsert_skill(name):
    pg_cur.execute(
        "INSERT INTO skill (name) VALUES (%s) ON CONFLICT DO NOTHING",
        (name,)
    )
    pg_cur.execute("SELECT skill_id FROM skill WHERE name = %s", (name,))
    return pg_cur.fetchone()[0]

def log_error(message):
    pg_cur.execute(
        "INSERT INTO log (log_data) VALUES (%s)",
        (message,)
    )
    pg_conn.commit()

def process_document(doc):
    try:
        platform_id = upsert_platform(doc["platform"])
        company_id = upsert_company(doc["company"])

        # 경력 정보 파싱 및 정수 변환
        exp = doc.get("experience", {})
        raw_min = exp.get("min_years", 0)
        raw_max = exp.get("max_years", 0)
        try:
            min_years = int(raw_min)
        except (TypeError, ValueError):
            min_years = 0
        try:
            max_years = int(raw_max)
        except (TypeError, ValueError):
            max_years = min_years

        # 위치 문자열 조합
        loc = doc.get("location", {})
        location_str = loc.get("city", "")
        if loc.get("district"):
            location_str += " " + loc["district"]

        # crawled_at 처리
        raw_crawled = doc.get("crawled_at")
        if isinstance(raw_crawled, dict) and "$date" in raw_crawled:
            crawled_at = datetime.fromisoformat(raw_crawled["$date"].replace("Z", "+00:00"))
        elif isinstance(raw_crawled, str):
            crawled_at = datetime.fromisoformat(raw_crawled.replace("Z", "+00:00"))
        else:
            crawled_at = raw_crawled  # 이미 datetime 객체인 경우

        # 공고 삽입
        pg_cur.execute(
            """
            INSERT INTO job_postings
            (platform_id, company_id, job_id, title, job_type, location,
             experience_min, experience_max, education, url, crawled_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO NOTHING
            RETURNING posting_id
            """,
            (
                platform_id,
                company_id,
                doc.get("job_id"),
                doc.get("job_title"),
                doc.get("work_type"),
                location_str,
                min_years,
                max_years,
                doc.get("education"),
                doc.get("job_url"),
                crawled_at
            )
        )
        result = pg_cur.fetchone()
        if result:
            posting_id = result[0]
        else:
            pg_cur.execute("SELECT posting_id FROM job_postings WHERE job_id = %s", (doc.get("job_id"),))
            posting_id = pg_cur.fetchone()[0]

        # 기술 스택 삽입
        for skill_name in doc.get("tech_stack", {}).get("raw_list", []):
            skill_id = upsert_skill(skill_name)
            pg_cur.execute(
                """
                INSERT INTO job_posting_skill
                (posting_id, company_id, skill_id, platform_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (posting_id, company_id, skill_id, platform_id)
            )

        pg_conn.commit()
        logger.info(f"Processed job_id={doc.get('job_id')} posting_id={posting_id}")

    except Exception as e:
        pg_conn.rollback()
        error_msg = f"Error processing job_id={doc.get('job_id')}: {e}"
        logger.error(error_msg)
        log_error(error_msg)

def run_etl():
    for doc in mdb.job_postings.find({}):
        process_document(doc)

if __name__ == "__main__":
    run_etl()
    pg_cur.close()
    pg_conn.close()
