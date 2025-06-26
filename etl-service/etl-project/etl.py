import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import psycopg2

# 환경변수 로드
load_dotenv()
os.environ.pop('PGPASSFILE', None)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# 환경변수 출력 (디버깅용)
print("'POSTGRES_SERVER' →", repr(os.getenv("POSTGRES_SERVER")))
print("'POSTGRES_PORT'   →", repr(os.getenv("POSTGRES_PORT")))
print("'POSTGRES_DB'     →", repr(os.getenv("POSTGRES_DB")))
print("'POSTGRES_USER'   →", repr(os.getenv("POSTGRES_USER")))
print("'POSTGRES_PASSWORD'→", repr(os.getenv("POSTGRES_PASSWORD")))

# MongoDB 연결
mongo = MongoClient(os.getenv("MONGO_URI"))
mdb = mongo[os.getenv("MONGO_DB")]

# PostgreSQL 연결 (client_encoding=UTF8, lc_messages=C 강제)
print("'POSTGRES_PASSWORD'→", repr(os.getenv("POSTGRES_PASSWORD")))
pg_conn = psycopg2.connect(
    host=os.getenv('POSTGRES_SERVER'),
    port=os.getenv('POSTGRES_PORT'),
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    client_encoding=os.getenv('PGCLIENTENCODING', 'UTF8')
)
pg_cur = pg_conn.cursor()

# --------------------------------------------------
# 1) DDL 생성 (없으면 테이블 만들기)
# --------------------------------------------------
ddl_statements = [
    """
    CREATE TABLE IF NOT EXISTS platform (
        platform_id   SERIAL PRIMARY KEY,
        platform_name VARCHAR(50) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS company (
        company_id      SERIAL PRIMARY KEY,
        name            VARCHAR(100) UNIQUE,
        size            VARCHAR(20),
        industry        VARCHAR(100),
        description     TEXT,
        sales           VARCHAR(50)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS job_postings (
        posting_id   BIGSERIAL PRIMARY KEY,
        platform_id  INT      REFERENCES platform(platform_id),
        company_id   INT      REFERENCES company(company_id),
        job_id       VARCHAR(50) UNIQUE,
        title        VARCHAR(200),
        job_type     VARCHAR(50),
        raw_text     VARCHAR(200),
        min_years    INT,
        max_years    INT,
        education    VARCHAR(20),
        tech_stack   VARCHAR(200),
        data_role    BOOLEAN,
        url          VARCHAR(500),
        apply_end    VARCHAR(10),
        crawled_at   TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS skill (
        skill_id SERIAL PRIMARY KEY,
        name     VARCHAR(50) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS job_posting_skill (
        posting_id BIGINT    REFERENCES job_postings(posting_id),
        skill_id   INT       REFERENCES skill(skill_id),
        skill_type VARCHAR(20),
        PRIMARY KEY (posting_id, skill_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS location (
        location_id    SERIAL PRIMARY KEY,
        city           VARCHAR(50),
        district       VARCHAR(50),
        detail_address VARCHAR(200),
        posting_id     BIGINT REFERENCES job_postings(posting_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS experience (
        exp_id     SERIAL PRIMARY KEY,
        posting_id BIGINT NOT NULL REFERENCES job_postings(posting_id),
        raw_text   VARCHAR(50),
        min_years  INT,
        max_years  INT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS position (
        pos_id     SERIAL PRIMARY KEY,
        posting_id BIGINT NOT NULL REFERENCES job_postings(posting_id),
        raw_text   VARCHAR(200)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS position_list (
        id     SERIAL PRIMARY KEY,
        pos_id INT    REFERENCES position(pos_id),
        role   VARCHAR(50)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS position_normalized (
        norm_id            SERIAL PRIMARY KEY,
        pos_id             INT     REFERENCES position(pos_id),
        primary_category   VARCHAR(50),
        secondary_category VARCHAR(50),
        primary_label      VARCHAR(50),
        secondary_label    VARCHAR(50),
        confidence         VARCHAR(20),
        is_data_role       BOOLEAN
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS log (
        log_id   SERIAL PRIMARY KEY,
        log_data TEXT,
        log_date TIMESTAMP DEFAULT NOW()
    )
    """
]

for stmt in ddl_statements:
    pg_cur.execute(stmt)
pg_conn.commit()

# --------------------------------------------------
# 2) Upsert 헬퍼 함수
# --------------------------------------------------
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
          SET
            size        = EXCLUDED.size,
            industry    = COALESCE(EXCLUDED.industry,    company.industry),
            description = COALESCE(EXCLUDED.description, company.description),
            sales       = COALESCE(EXCLUDED.sales,       company.sales)
        """,
        (
            info.get("name"),
            info.get("size"),
            info.get("industry"),
            info.get("description"),
            info.get("sales"),
        )
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

# --------------------------------------------------
# 3) 문서 처리 함수
# --------------------------------------------------
def process_document(doc):
    try:
        platform_id = upsert_platform(doc["platform"])
        company_id  = upsert_company(doc["company"])

        # 경력 파싱
        exp = doc.get("experience", {})
        try: min_years = int(exp.get("min_years", 0))
        except: min_years = None
        try: max_years = int(exp.get("max_years", 0))
        except: max_years = None

        # crawled_at 파싱
        raw_crawled = doc.get("crawled_at")
        if isinstance(raw_crawled, dict) and "$date" in raw_crawled:
            crawled_at = datetime.fromisoformat(raw_crawled["$date"].replace("Z", "+00:00"))
        else:
            crawled_at = None

        # job_postings 삽입
        pg_cur.execute(
            """
            INSERT INTO job_postings
              (platform_id, company_id, job_id, title, job_type,
               raw_text, min_years, max_years, education, tech_stack,
               data_role, url, apply_end, crawled_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO NOTHING
            RETURNING posting_id
            """,
            (
                platform_id,
                company_id,
                doc.get("job_id"),
                doc.get("job_title"),
                doc.get("work_type"),
                doc["position"].get("raw_text"),
                min_years,
                max_years,
                doc.get("education"),
                ",".join(doc.get("tech_stack", {}).get("raw_list", [])),
                doc["position"]["normalized"].get("is_data_role", False),
                doc.get("job_url"),
                doc.get("apply_end"),
                crawled_at
            )
        )
        row = pg_cur.fetchone()
        if row:
            posting_id = row[0]
        else:
            pg_cur.execute("SELECT posting_id FROM job_postings WHERE job_id = %s", (doc.get("job_id"),))
            posting_id = pg_cur.fetchone()[0]

        # location 삽입
        loc = doc.get("location", {})
        pg_cur.execute(
            "INSERT INTO location (city, district, detail_address, posting_id) VALUES (%s, %s, %s, %s)",
            (loc.get("city"), loc.get("district"), loc.get("detail_address"), posting_id)
        )

        # experience 삽입
        pg_cur.execute(
            "INSERT INTO experience (posting_id, raw_text, min_years, max_years) VALUES (%s, %s, %s, %s)",
            (posting_id, exp.get("raw_text"), min_years, max_years)
        )

        # position/position_list/position_normalized 삽입
        pg_cur.execute(
            "INSERT INTO position (posting_id, raw_text) VALUES (%s, %s) RETURNING pos_id",
            (posting_id, doc["position"].get("raw_text"))
        )
        pos_id = pg_cur.fetchone()[0]

        for role in doc["position"].get("raw_list", []):
            pg_cur.execute(
                "INSERT INTO position_list (pos_id, role) VALUES (%s, %s)",
                (pos_id, role)
            )

        norm = doc["position"].get("normalized", {})
        pg_cur.execute(
            """
            INSERT INTO position_normalized
              (pos_id, primary_category, secondary_category,
               primary_label, secondary_label, confidence, is_data_role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pos_id,
                norm.get("primary_category"),
                norm.get("secondary_category"),
                norm.get("primary_label"),
                norm.get("secondary_label"),
                norm.get("confidence"),
                norm.get("is_data_role", False)
            )
        )

        # skill & job_posting_skill 삽입
        for sk in doc.get("tech_stack", {}).get("raw_list", []):
            skill_id = upsert_skill(sk)
            pg_cur.execute(
                "INSERT INTO job_posting_skill (posting_id, skill_id, skill_type) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (posting_id, skill_id, "tech")
            )
        for sk in doc.get("preferred_experience", {}).get("raw_list", []):
            skill_id = upsert_skill(sk)
            pg_cur.execute(
                "INSERT INTO job_posting_skill (posting_id, skill_id, skill_type) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (posting_id, skill_id, "preferred")
            )

        pg_conn.commit()
        logger.info(f"Processed job_id={doc.get('job_id')} → posting_id={posting_id}")

    except Exception as e:
        pg_conn.rollback()
        err = f"Error processing job_id={doc.get('job_id')}: {e}"
        logger.error(err)
        log_error(err)

# --------------------------------------------------
# 4) ETL 실행
# --------------------------------------------------
def run_etl():
    for doc in mdb.job_postings.find({}):
        process_document(doc)

if __name__ == "__main__":
    run_etl()
    pg_cur.close()
    pg_conn.close()
