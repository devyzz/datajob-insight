#db 연결/데이터 불러오기 함수 모음
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st
from collections import Counter
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def get_engine():
    """PostgreSQL 데이터베이스 연결을 위한 엔진을 생성합니다."""
    try:
        # 환경변수에서 DB 연결 정보 가져오기 
        db_user = os.getenv('POSTGRES_USER')
        db_password = os.getenv('POSTGRES_PASSWORD')
        db_host = os.getenv('POSTGRES_SERVER')
        db_port = os.getenv('POSTGRES_PORT')
        db_name = os.getenv('POSTGRES_DB')
        
        # 필수 환경변수 검증
        if not all([db_user, db_password, db_host, db_port, db_name]):
            missing_vars = []
            if not db_user: missing_vars.append('POSTGRES_USER')
            if not db_password: missing_vars.append('POSTGRES_PASSWORD')
            if not db_host: missing_vars.append('POSTGRES_SERVER')
            if not db_port: missing_vars.append('POSTGRES_PORT')
            if not db_name: missing_vars.append('POSTGRES_DB')
            
            raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        
        # 포트 번호가 올바른 정수인지 검증
        try:
            db_port = int(db_port)
        except ValueError:
            raise ValueError(f"POSTGRES_PORT가 올바른 숫자가 아닙니다: {db_port}")
        
        # Docker 환경에서는 서비스 이름으로 연결
        if os.getenv('DOCKER_ENV') == 'true' or os.getenv('DOCKER_ENV') == 'false':
            db_host = 'postgres'
        
        # 연결 정보 로깅 (디버깅용)
        print(f"Connecting to PostgreSQL: {db_host}:{db_port}/{db_name}")
        
        engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
        return engine
    except Exception as e:
        st.error(f"DB 연결에 실패했습니다: {e}")
        return None

@st.cache_data(ttl=3600)
def load_data():
    engine = get_engine()
    if engine is not None:
        try:
            # 먼저 간단한 쿼리로 테스트
            test_query = "SELECT COUNT(*) FROM jobposting;"
            result = pd.read_sql(test_query, engine)
            print(f"테이블 레코드 수: {result.iloc[0, 0]}")
            
            # 전체 데이터 로드
            query = """
            SELECT 
                posting_id,
                company_id,
                platform_id,
                title,
                job_type,
                location,
                position,
                experience_min,
                experience_max,
                education,
                tech_stack,
                is_data_job,
                url,
                apply_end_date,
                crawled_at
            FROM jobposting;
            """
            df = pd.read_sql(query, engine)
            print(f"로드된 데이터: {len(df)} 행")
            
            # location에서 구 정보 추출 (Python에서 처리)
            if not df.empty and 'location' in df.columns:
                df['location_district'] = df['location'].apply(
                    lambda x: x.split(' ')[1] if x and ' ' in x else x
                )
            
            # experience_min을 숫자로 변환
            df['experience_min_years'] = df['experience_min'].apply(
                lambda x: 0 if x == '신입' else 
                int(''.join(filter(str.isdigit, x))) if x and '년' in x else 0
            )
            
            return df
        except Exception as e:
            st.error(f"데이터 로딩에 실패했습니다: {e}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
            return pd.DataFrame()
    return pd.DataFrame()

def get_tech_stack_counts(series):
    """
    'tech_stack' 컬럼(Series)을 받아서 기술 스택별 빈도를 계산합니다.
    예: 'Python, Java, SQL' -> Python, Java, SQL로 분리하여 카운트
    """
    tech_list = []
    for item in series.dropna():
        # 쉼표, 슬래시, 공백 등 다양한 구분자를 처리
        techs = [tech.strip() for tech in item.replace('/', ',').replace(' ', ',').split(',') if tech.strip()]
        tech_list.extend(techs)
    
    return Counter(tech_list)

def get_company_size_specs():
    """기업 규모별 요구 스펙 통계를 가져옵니다."""
    engine = get_engine()
    query = """
    SELECT 
        '대기업' as company_size,
        COUNT(*) as job_count,
        STRING_AGG(DISTINCT tech_stack, ', ') as tech_stacks,
        AVG(
            CASE 
                WHEN experience_min = '신입' THEN 0
                WHEN experience_min LIKE '%년%' THEN 
                    CAST(REGEXP_REPLACE(experience_min, '[^0-9]', '', 'g') AS INTEGER)
                ELSE 0
            END
        ) as avg_min_experience,
        MODE() WITHIN GROUP (ORDER BY education) as most_common_education
    FROM jobposting
    WHERE company_id IN (101, 102, 103)
    GROUP BY '대기업'
    """
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"get_company_size_specs 오류: {e}")
        return pd.DataFrame()

def get_data_job_analysis():
    """데이터 직군 여부에 따른 분석 데이터를 가져옵니다."""
    engine = get_engine()
    query = """
    SELECT 
        is_data_job,
        COUNT(*) as job_count,
        STRING_AGG(DISTINCT tech_stack, ', ') as tech_stacks,
        AVG(
            CASE 
                WHEN experience_min = '신입' THEN 0
                WHEN experience_min LIKE '%년%' THEN 
                    CAST(REGEXP_REPLACE(experience_min, '[^0-9]', '', 'g') AS INTEGER)
                ELSE 0
            END
        ) as avg_min_experience,
        '대기업' as company_sizes
    FROM jobposting
    GROUP BY is_data_job
    """
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"get_data_job_analysis 오류: {e}")
        return pd.DataFrame()

def get_skill_analysis():
    """기술 스택 분석 데이터를 가져옵니다."""
    engine = get_engine()
    query = """
    SELECT 
        tech_stack as skill_name,
        COUNT(*) as usage_count,
        '기술스택' as skill_type
    FROM jobposting
    WHERE tech_stack IS NOT NULL
    GROUP BY tech_stack
    ORDER BY usage_count DESC
    """
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"get_skill_analysis 오류: {e}")
        return pd.DataFrame()

def get_position_analysis():
    """포지션 분석 데이터를 가져옵니다."""
    engine = get_engine()
    query = """
    SELECT 
        position as position_name,
        COUNT(*) as job_count,
        CASE 
            WHEN position LIKE '%데이터%' OR position LIKE '%AI%' OR position LIKE '%ML%' THEN '데이터/AI'
            WHEN position LIKE '%백엔드%' OR position LIKE '%서버%' THEN '백엔드'
            WHEN position LIKE '%프론트%' OR position LIKE '%클라이언트%' THEN '프론트엔드'
            ELSE '기타'
        END as primary_category,
        is_data_job
    FROM jobposting
    GROUP BY position, is_data_job
    ORDER BY job_count DESC
    """
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"get_position_analysis 오류: {e}")
        return pd.DataFrame()